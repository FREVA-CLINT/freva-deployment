#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF
Usage: $0 --engine <docker|podman> --old-parent-dir <path> --project-name <name>

Options:
  --engine           docker, podman or conda
  --old-parent-dir   Path to old bind-mounted data
  --project-name     Project name prefix for volumes
EOF
  exit 1
}

# Setup
BACKUP_DIR="$(mktemp -d /tmp/freva-migration-XXXXXX)"
FAILED_RESTORE=()
MIGRATIONS=()

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --engine) ENGINE="$2"; shift 2 ;;
    --old-parent-dir) OLD_PARENT_DIR="$2"; shift 2 ;;
    --project-name) PROJECT_NAME="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
done

[[ -z "${ENGINE:-}" || -z "${OLD_PARENT_DIR:-}" || -z "${PROJECT_NAME:-}" ]] && usage
[[ "$ENGINE" != "docker" && "$ENGINE" != "podman" && "$ENGINE" != "conda" ]] && { echo "❌ Engine must be 'docker' 'podman or 'conda''"; exit 1; }

# Normalize service folder names
normalize_service_name() {
  case "$1" in
    conda) echo "conda" ;;
    web_service) echo "freva-web" ;;
    freva_rest) echo "mongodb" ;;
    databro*) echo "mongodb" ;;
    solr_service) echo "solr" ;;
    vault_service) echo "vault" ;;
    db_service) echo "db" ;;
    *) echo "$1" ;;
  esac
}

# Migrate one volume
migrate_volume() {
  local service="$1"
  local src_path="$2"
  local del_path="$3"
  local vol="${PROJECT_NAME}-${service}_data"
  local volume_backup="${BACKUP_DIR}/${vol}.tar.gz"
  local status="success"

  echo ""
  echo "🔧 Migrating $service → $vol"
  echo "   📁 Source path: $src_path"

  MIGRATIONS+=("$service")
  if ! $ENGINE volume inspect "$vol" >/dev/null 2>&1; then
    echo "   📦 Creating volume: $vol"
    $ENGINE volume create "$vol" 1> /dev/null
  fi

  echo "   🗃️ Backing up volume to: $volume_backup"
  $ENGINE run --rm -v "$vol:/data:ro" -v "$BACKUP_DIR:/backup:Z" alpine \
    tar czf "/backup/$(basename "$volume_backup")" -C /data .

  if ! $ENGINE run --rm \
    -v "$vol:/data" \
    -v "$src_path:/backup:ro,Z" \
    alpine sh -c "cp -a /backup/. /data/"; then
    echo "   ❌ Migration failed, restoring to original bind-mount: $src_path"
    rm -rf "$src_path"/*
    if tar -xzf "$volume_backup" -C "$src_path"; then
      echo "   ✅ Restore successful."
    else
      echo "   ❌ Restore failed. Manual fix required: $src_path"
      FAILED_RESTORE+=("$src_path")
      status="failed"
    fi
  else
    echo "   ✅ Migration complete. Cleaning up backup."
    rm -f "$volume_backup"
    rm -r "$del_path"
  fi

}

get_container_cmd(){
    local order=(podman docker)
    local path=""
    for cmd in ${order[*]};do
        if [ "$(which $cmd 2> /dev/null)" ];then
            path=$cmd
            break
        fi
    done
    echo $path
}

migrate(){
    services=(db mongodb solr vault)
    for service in ${services[*]};do
        local conda_path="$OLD_PARENT_DIR/$PROJECT_NAME/conda/share/freva/$service"
        if [ ${ENGINE} != "conda" ];then
            if [ -d "$conda_path/data" ];then
                migrate_volume $service $conda_path/data $conda_path
            fi
        else
            local cmd=$(get_container_cmd)
            local vol="${PROJECT_NAME}_${service}_data"
            if ([ "$cmd" ] && [ ! -d "$conda_path/data" ]);then
                mkdir -p ${conda_path}/{logs,config}
                vol_path=$($cmd volume inspect ${vol} --format='{{.Mountpoint}}' 2> /dev/null)
                if [ -d "${vol_path}" ];then
                    echo 🔧 Migrating vol: ${service} → conda
                    echo "   📁 Source path: ${vol_path}"
                    cp -r ${vol_path} "${conda_path}/data"
                    echo "   📦 Deleting volume: ${vol}"
                    $cmd volume rm -f ${vol} 1> /dev/null
                    echo ""
                fi
            fi
        fi
    done
}

# Detect services and their volume types
detect_legacy_services() {
  local base_path="$OLD_PARENT_DIR/$PROJECT_NAME"
  for path in "$base_path"/*; do
    [[ -d "$path" ]] || continue
    local dir
    dir="$(basename "$path")"
    local service
    service="$(normalize_service_name "$dir")"
    case $service in
        freva-web) rm -r $path;;
        solr) echo -e "$service\t${path}/data\t${path}";;
        mongodb) echo -e "$service\t${path}/stats\t${path}";;
        vault) echo -e "$service\t${path}\t${path}";;
        db) echo -e "$service\t${path}\t${path}";;
        compose*) ;;
        conda*) ;;
        *) rm -fr $path
    esac
  done
}

# Migrate one volume
migrate_conda_legacy() {
  local service="$1"
  local src_path="$2"
  local del_path="$3"
  local vol="${OLD_PARENT_DIR}/${PROJECT_NAME}/conda/share/freva/$service"
  local volume_backup="${BACKUP_DIR}/${service}.tar.gz"
  local status="success"

  echo ""
  echo "🔧 Migrating $service → conda"
  echo "   📁 Source path: $src_path"
  mkdir -p "${vol}"/{logs,config}
  MIGRATIONS+=("$service")
  cp -r "$src_path" "$vol/data"
  rm -r "$del_path"

}

# Main loop: one-by-one migration
while IFS=$'\t' read -r service path del_path; do
  if [ "$ENGINE" = "conda" ];then
      migrate_conda_legacy "$service" "$path" "$del_path"
  else
      migrate_volume "$service" "$path" "$del_path"
  fi
done < <(detect_legacy_services)
if [ "${#MIGRATIONS[@]}" -eq 0 ];then
    migrate
fi
if [ "${#FAILED_RESTORE[@]}" -ne 0 ]; then
  echo ""
  echo "❌ Restore failed for the following paths:"
  for path in "${FAILED_RESTORE[@]}"; do
    echo "   - $path"
  done
fi

# Cleanup
rm -rf "$BACKUP_DIR"

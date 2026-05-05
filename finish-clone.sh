#!/bin/sh

set -eu

stderr() {
    printf -- '%s\n' "${@}"
} 1>&2

assign_loop_vars() {
    sm_name="${1}"
    sm_path="${2}"
    sm_branch="${3}"
}

is_nested() {
    case "${1}" in
        */*) return 0 ;;
        *) return 1 ;;
    esac
}

filter_submodule() {
    assign_loop_vars "${@}"

    if [ "${sm_name}" = "${SABR_NAME}" ]; then
        return 0
    fi

    if ! is_nested "${sm_path}"; then
        return 0
    fi

    return 1
}

process_submodules() (
    PARSE_SUB_AWK='{
        name = $1;
        sub(/^submodule\./, "", name);
        sub(/\.path$/, "", name);

        path = $0;
        sub(/^[^ ]+ /, "", path);

        print name;
        print path;
    }'

    git config --file '.gitmodules' --get-regexp 'path' | \
        awk "${PARSE_SUB_AWK}" | \
    while read -r name; do
        read -r path
        branch="$(git config --file '.gitmodules' --get "submodule.${name}.branch")"
        "${1}" "${name}" "${path}" "${branch}"
        if [ 1 -eq "${break_loop:-0}" ]; then
            break
        fi
    done
)

find_sabr_branch() {
    assign_loop_vars "${@}"

    if [ 'sabr' = "${sm_path}" ]; then
        echo "${sm_branch}"
        break_loop=1
    fi
}

find_sabr_name() {
    assign_loop_vars "${@}"

    if [ 'sabr' = "${sm_path}" ]; then
        echo "${sm_name}"
        break_loop=1
    fi
}

update_forks() {
    assign_loop_vars "${@}"
    if filter_submodule "${@}"; then return 0; fi

    echo "Updating ${sm_path} referencing ${SABR_NAME}..."
    git submodule update --init --progress --no-single-branch --rebase \
        --reference ".git/modules/${SABR_NAME}" -- "${sm_path}"

    (cd "${sm_path}" && git switch "${sm_branch}")
}

verify_alternates() {
    assign_loop_vars "${@}"
    if filter_submodule "${@}"; then return 0; fi

    alt_file=".git/modules/${sm_name}/objects/info/alternates"
    if [ -f "${alt_file}" ]; then
        raw="$(head -n 1 "${alt_file}")"
        short="$(realpath --relative-base=. "${raw}" 2>/dev/null|| printf -- '%s' "${raw}")"
        echo "Verification: ${sm_path} is borrowing from ${short}"
    else
        stderr "Verification Failure: ${sm_path} is NOT using an alternate store."
    fi
}

# Register all submodules
git submodule init

# Synchronize all submodules
git submodule sync

# Fully populate primary data source
echo 'Fetching primary objects for sabr...'
git submodule update --init --progress --no-single-branch --rebase -- 'sabr'

SABR_NAME="$(process_submodules find_sabr_name)"

if [ -z "${SABR_NAME}" ]; then
    stderr "Error: Could not find submodule name for path 'sabr'"
    exit 1
fi

if ! [ -d ".git/modules/${SABR_NAME}" ]; then
    stderr "Error: Primary submodule directory '.git/modules/${SABR_NAME}' not found."
    exit 1
fi

# Add a warning comment to the local git config
git config submodule."${SABR_NAME}".comment 'DO NOT DEINIT: Shared object store for forks'

SABR_BRANCH="$(process_submodules find_sabr_branch)"
(cd sabr && git switch "${SABR_BRANCH}")

# Process nested submodules referencing sabr
process_submodules update_forks

# Final verification
process_submodules verify_alternates

echo 'Infrastructure populated and verified successfully.'


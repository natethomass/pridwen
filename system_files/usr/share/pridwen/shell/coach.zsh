# Pridwen Coach hook for zsh. Sourced by /etc/zshrc for interactive shells.
# After every command it sends one JSON line (command, exit code, duration,
# cwd; never output) to the per-user daemon and prints the daemon's one-line
# hint, if any. See /usr/share/doc/pridwen/coach.md. `pridwen quiet` silences it.
[[ -o interactive ]] || return 0
[[ -x /usr/libexec/pridwen-coach-send ]] || return 0
[[ -n "${PRIDWEN_COACH_OFF:-}" ]] && return 0

zmodload zsh/datetime 2>/dev/null

typeset -g __pridwen_cmd=""
typeset -g __pridwen_t0=""

__pridwen_preexec() {
    __pridwen_cmd="$1"
    __pridwen_t0="$EPOCHREALTIME"
}

__pridwen_json_escape() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//$'\n'/\\n}"
    s="${s//$'\t'/\\t}"
    s="${s//$'\r'/}"
    printf '%s' "$s"
}

__pridwen_precmd() {
    local rc=$?
    local cmd="$__pridwen_cmd" ms=0
    [[ -z "$cmd" ]] && return 0
    __pridwen_cmd=""
    if [[ -n "$__pridwen_t0" && -n "$EPOCHREALTIME" ]]; then
        ms=$(( int((EPOCHREALTIME - __pridwen_t0) * 1000) ))
        (( ms < 0 )) && ms=0
    fi
    __pridwen_t0=""
    [[ ${#cmd} -gt 4000 ]] && cmd="${cmd[1,4000]}"
    /usr/libexec/pridwen-coach-send "{\"v\":1,\"cmd\":\"$(__pridwen_json_escape "$cmd")\",\"exit\":${rc},\"ms\":${ms},\"cwd\":\"$(__pridwen_json_escape "$PWD")\",\"shell\":\"zsh\",\"pid\":$$}"
    return 0
}

autoload -Uz add-zsh-hook
add-zsh-hook preexec __pridwen_preexec
add-zsh-hook precmd __pridwen_precmd

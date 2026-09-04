# Pridwen Coach hook for bash. Sourced by /etc/bashrc for interactive shells.
# After every command it sends one JSON line (command, exit code, duration,
# cwd; never output) to the per-user daemon and prints the daemon's one-line
# hint, if any. See /usr/share/doc/pridwen/coach.md. `pridwen quiet` silences it.
[[ $- == *i* ]] || return 0
[[ -x /usr/libexec/pridwen-coach-send ]] || return 0
[[ -n "${PRIDWEN_COACH_OFF:-}" ]] && return 0

__pridwen_last_hist=""
__pridwen_t0=""

# DEBUG fires before each simple command; record the start time once per
# command line (the first DEBUG after a prompt).
__pridwen_preexec() {
    [[ -n "${COMP_LINE:-}" ]] && return 0
    # Skip the prompt's own commands (ours and anything else in PROMPT_COMMAND,
    # e.g. __vte_prompt_command) so the timer starts at the user's command.
    [[ "$BASH_COMMAND" == "__pridwen_precmd" ]] && return 0
    [[ ${#BASH_COMMAND} -ge 6 && "${PROMPT_COMMAND[*]:-}" == *"$BASH_COMMAND"* ]] && return 0
    [[ -z "$__pridwen_t0" ]] && __pridwen_t0="${EPOCHREALTIME:-$(date +%s.%N)}"
    return 0
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
    local hist cmd t1 ms
    hist="$(HISTTIMEFORMAT='' builtin history 1)"
    # A new prompt without a new history entry means an empty line or a
    # duplicate suppressed by HISTCONTROL: nothing to report.
    if [[ -z "$hist" || "$hist" == "$__pridwen_last_hist" ]]; then
        __pridwen_t0=""
        return 0
    fi
    __pridwen_last_hist="$hist"
    cmd="${hist#*[0-9]  }"
    cmd="${cmd#"${cmd%%[![:space:]]*}"}"
    t1="${EPOCHREALTIME:-$(date +%s.%N)}"
    if [[ -n "$__pridwen_t0" ]]; then
        ms=$(( (${t1%.*} - ${__pridwen_t0%.*}) * 1000 + (10#${t1#*.} / 1000 - 10#${__pridwen_t0#*.} / 1000) ))
        (( ms < 0 )) && ms=0
    else
        ms=0
    fi
    __pridwen_t0=""
    [[ ${#cmd} -gt 4000 ]] && cmd="${cmd:0:4000}"
    /usr/libexec/pridwen-coach-send "{\"v\":1,\"cmd\":\"$(__pridwen_json_escape "$cmd")\",\"exit\":${rc},\"ms\":${ms},\"cwd\":\"$(__pridwen_json_escape "$PWD")\",\"shell\":\"bash\",\"pid\":$$}"
    return 0
}

trap '__pridwen_preexec' DEBUG
if [[ -z "${PROMPT_COMMAND:-}" ]]; then
    PROMPT_COMMAND="__pridwen_precmd"
elif [[ "$PROMPT_COMMAND" != *__pridwen_precmd* ]]; then
    PROMPT_COMMAND="__pridwen_precmd;${PROMPT_COMMAND}"
fi

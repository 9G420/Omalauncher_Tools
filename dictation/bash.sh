# Insert at the cursor, preserving any existing input. Never press Enter.
_oma_speak_insert() {
  local dictated
  [[ -f $HOME/.cache/oma-speak/latest.txt ]] || return 0
  dictated=$(< "$HOME/.cache/oma-speak/latest.txt")
  READLINE_LINE="${READLINE_LINE:0:READLINE_POINT}${dictated}${READLINE_LINE:READLINE_POINT}"
  READLINE_POINT=$((READLINE_POINT + ${#dictated}))
}
bind -x '"\C-g":_oma_speak_insert'

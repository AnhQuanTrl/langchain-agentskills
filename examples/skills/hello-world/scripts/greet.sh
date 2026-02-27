#!/bin/bash
# Usage: greet.sh <name> [style]
# Generates a greeting for the given name in the specified style.

NAME="${1:-World}"
STYLE="${2:-casual}"

case "$STYLE" in
    formal)
        echo "Good day, $NAME. It is a pleasure to make your acquaintance."
        ;;
    enthusiastic)
        echo "$NAME!! So awesome to meet you! 🎉"
        ;;
    casual|*)
        echo "Hey $NAME! What's up?"
        ;;
esac

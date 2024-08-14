#!/bin/sh

# entrypoint.sh
setup_feature() {
  echo "Build feature store.."
  source /usr/local/bin/activate py38 && python3 -m huixiangdou.service.feature_store
}

start_service() {
  echo "Starting service.."
  source /usr/local/bin/activate py38 && python3 -m huixiangdou.gradio
}

case "$1" in
  setup_feature)
    setup_feature
    ;;
  start_service)
    start_service
    ;;
  *)
    echo "Invalid command: $1"
    exit 1
    ;;
esac
REPO_NAME="test_repo"
poetry run adev repo $REPO_NAME -t autonomy
cd $REPO_NAME
poetry lock --no-update && poetry install
cp poetry.lock ../auto_dev/data/repo/templates/autonomy/

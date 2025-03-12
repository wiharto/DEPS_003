# the `update-function-configuration` overwrites the existing set envars.
# In order to *ADD* variables we need to read the existing envars and add to that.
# This command uses `jq` to read and transform the json result to an envar then update the lambda configuration

# create the updated envar set
export FUNCTION_NAME='user_tweets_producer'
export UPDATED_ENVIRONMNET_VARIABLES=$(aws lambda get-function-configuration --function-name ${FUNCTION_NAME} | \
    jq --compact-output ".Environment + {\"Variables\": (.Environment.Variables + {\"TWITTER_BEARER_TOKEN\": \"AAAAAAAAAAAAAAAAAAAAA.....\", \"TWITTER_USER_ID\": \"17471979\"})}")

# check
env | grep UPDATED_ENVIRONMNET_VARIABLES

# update current lambda configuration
aws lambda update-function-configuration --function-name ${FUNCTION_NAME} \
    --environment ${UPDATED_ENVIRONMNET_VARIABLES}

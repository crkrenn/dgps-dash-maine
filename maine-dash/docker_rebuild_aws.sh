docker buildx build --platform linux/amd64 -f ./Dockerfile -t democracygps/maine-dash:testamd .
docker tag "democracygps/maine-dash:testamd" "democracygps/maine-dash:latest"
docker push  "democracygps/maine-dash:latest"
aws ecs update-service  --cluster dash-app --service dash-app-service --region us-east-2  --force-new-deployment

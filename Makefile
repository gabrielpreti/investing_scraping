SCRAPPING_IMAGE_NAME = "gabrielpreti/investing_scrapping"
SCRAPPING_CONTAINER_NAME = "investing_scrapping_container"
MONGO_IMAGE_NAME = "mongo:4-xenial"
MONGO_CONTAINER_NAME = "stock_data_db"

STACK_NAME = "investing-scrapping-stack"
MY_IP = `dig +short myip.opendns.com @resolver1.opendns.com`
SSH_KEY_FILE = "~/Documents/aws_keys/pytradejobs.pem"

ifeq ($(MONGO_DATA_DIR),)
  MONGO_DATA_DIR = "/tmp/mongodb"
endif

AWS_INSTANCE_IP := `aws cloudformation  describe-stacks --stack-name=${STACK_NAME} --query "Stacks[0].Outputs[?OutputKey=='Ec2InstancePublicIp'].OutputValue" --output text`
DOCKER_HOST := 'tcp://localhost:2375'

configure-docker-to-aws-istance:
	$(eval DOCKER_HOST:=tcp://${AWS_INSTANCE_IP}:2375)





build-scrapping:
	docker build -t ${SCRAPPING_IMAGE_NAME} .

make push-scrapping:
	docker push ${SCRAPPING_IMAGE_NAME}

run-scrapping:
	DOCKER_HOST=${DOCKER_HOST} docker run -d --name ${SCRAPPING_CONTAINER_NAME} --link ${MONGO_CONTAINER_NAME}:${MONGO_CONTAINER_NAME}  ${SCRAPPING_IMAGE_NAME} python investing_data_collector.py --mongohost=${MONGO_CONTAINER_NAME}

run-scrapping-aws: configure-docker-to-aws-istance run-scrapping

stop-scrapping:
	DOCKER_HOST=${DOCKER_HOST} docker stop ${SCRAPPING_CONTAINER_NAME}

stop-scrapping-aws: configure-docker-to-aws-istance stop-scrapping

logs-scrapping:
	DOCKER_HOST=${DOCKER_HOST} docker logs ${SCRAPPING_CONTAINER_NAME} --follow=true --tail=1000

logs-scrapping-aws: configure-docker-to-aws-istance logs-scrapping

rm-scrapping:
	DOCKER_HOST=${DOCKER_HOST} docker rm ${SCRAPPING_CONTAINER_NAME}

rm-scrapping-aws: configure-docker-to-aws-istance rm-scrapping

rmi-scrapping:
	DOCKER_HOST=${DOCKER_HOST} docker rmi ${SCRAPPING_IMAGE_NAME}

rmi-scrapping-aws: configure-docker-to-aws-istance rmi-scrapping

ssh-scrapping:
	DOCKER_HOST=${DOCKER_HOST} docker exec -it ${SCRAPPING_CONTAINER_NAME} /bin/bash

ssh-scrapping-aws: configure-docker-to-aws-istance ssh-scrapping

wait-scrapping-to-finish:
	DOCKER_HOST=${DOCKER_HOST} docker wait ${SCRAPPING_CONTAINER_NAME}

wait-scrapping-to-finish-aws: configure-docker-to-aws-istance wait-scrapping-to-finish



run-mongo:
	DOCKER_HOST=${DOCKER_HOST} docker run --name ${MONGO_CONTAINER_NAME} -v ${MONGO_DATA_DIR}:/data/db -p 27017:27017 -d ${MONGO_IMAGE_NAME}

configure-mongo-to-aws:
	$(eval MONGO_DATA_DIR:=/mnt/ebs_data/mongodata)

run-mongo-aws: configure-docker-to-aws-istance configure-mongo-to-aws run-mongo

stop-mongo:
	DOCKER_HOST=${DOCKER_HOST} docker stop ${MONGO_CONTAINER_NAME}

stop-mongo-aws: configure-docker-to-aws-istance stop-mongo

start-mongo:
	DOCKER_HOST=${DOCKER_HOST} docker start ${MONGO_CONTAINER_NAME}

start-mongo-aws: configure-docker-to-aws-istance start-mongo

rm-mongo:
	DOCKER_HOST=${DOCKER_HOST} docker rm ${MONGO_CONTAINER_NAME}

rm-mongo-aws: configure-docker-to-aws-istance rm-mongo

ssh-mongo:
	DOCKER_HOST=${DOCKER_HOST} docker exec -it ${MONGO_CONTAINER_NAME} /bin/bash

ssh-mongo-aws: configure-docker-to-aws-istance ssh-mongo





create-aws-stack:
	aws cloudformation create-stack --stack-name=${STACK_NAME} --template-body=file://./investingscrapping_aws.yaml --parameters ParameterKey=MyIp,ParameterValue=${MY_IP} ParameterKey=ProjectName,ParameterValue='Investing Scrapping' ParameterKey=NeedsEBSVolume,ParameterValue=true ParameterKey=EC2MarketType,ParameterValue='On-demand' ParameterKey=VpcCIDR,ParameterValue=10.193.0.0/16 ParameterKey=Subnet1CIDR,ParameterValue=10.193.10.0/24 ParameterKey=EC2KeyName,ParameterValue=pytradejobs ParameterKey=EBSVolumeId,ParameterValue='vol-0720dcb52f88d1c3e'

wait-aws-stack-creation:
	set -e ;\
	STATUS=$$(aws cloudformation  describe-stacks --stack-name=${STACK_NAME} --query 'Stacks[0].StackStatus' --output text) ;\
	echo $${STATUS} ;\
	while [ $${STATUS} = "CREATE_IN_PROGRESS" ] ; do \
		echo "$${STATUS} ... " ; \
		STATUS=$$(aws cloudformation  describe-stacks --stack-name=${STACK_NAME} --query 'Stacks[0].StackStatus' --output text) ;\
	done; \
	true

get-aws-stack_status:
	aws cloudformation  describe-stacks --stack-name=${STACK_NAME} --query 'Stacks[0].StackStatus' --output text

ssh-into-instance:
	set -e ;\
	INSTANCE_IP=$$(aws cloudformation  describe-stacks --stack-name=${STACK_NAME} --query "Stacks[0].Outputs[?OutputKey=='Ec2InstancePublicIp'].OutputValue" --output text) ;\
	ssh -i ${SSH_KEY_FILE} ec2-user@$${INSTANCE_IP} ;\

delete-aws-stack:
	aws cloudformation delete-stack --stack-name=${STACK_NAME}




sleep:
	sleep 30s

create-aws-stack-and-run: create-aws-stack sleep wait-aws-stack-creation sleep sleep run-mongo-aws sleep run-scrapping-aws wait-scrapping-to-finish-aws delete-aws-stack
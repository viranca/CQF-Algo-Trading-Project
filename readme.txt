
###to run overal docker-compose:
cd ".\(AL) VIRANCA BALSINGH CODE"

docker-compose -f Research/docker-compose-research.yml up --build

###to run individual Dockerfile.postgres:
cd ".\(AL) VIRANCA BALSINGH CODE"

docker build -t postgres_research -f Research/postgresql/Dockerfile.postgres .

docker run -d --name postgres-container -p 5432:5432 postgres_research



###run ib gateway
cd ".\(AL) VIRANCA BALSINGH CODE"


docker-compose -f Research/interactive_brokers/ib-gateway-docker-master/docker-compose.yml up --build


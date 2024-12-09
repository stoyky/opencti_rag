# OpenCTI RAG system 
This repository contains the OpenCTI RAG System as is described on [my blog](https://www.remyjaspers.com/blog/opencti_rag/).

## Installation instructions
1. Make sure to have a [dockerized OpenCTI instance](https://github.com/OpenCTI-Platform/docker) up and running. I'm assuming the network it creates is *opencti_default*. 
2. Start up the Ollama Docker and pull the Mistral-7B Instruct model:
```bash
$ cd ollama_docker
$ docker-compose up -d 
$ docker exec -it ollama ollama run mistral:7b-instruct
```
3. Configure the `docker-compose.yml` settings and set the correct OPENCTI_TOKEN and CONNECTOR_ID (generated UUID). *Do not forget to create a connector user in OpenCTI*. Then start the OpenCTI RAG connector:
```bash
$ cd opencti_rag_connector
$ docker-compose up -d --build
```
4. Check the OpenCTI RAG connector logs to check if the reports are inserted into Elasticsearch. You can use the following command to view the indices and the number of documents in the `octi_rag` index. 
```
http://localhost:9200/_cat/indices?v
```
5. Start the StreamLit UI
```
$ cd opencti_rag_ui
$ docker-compose up -d --build
```
6. If all went well, go to `http://localhost:8501` and the StreamLit UI should be presented to you. 

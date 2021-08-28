# Dockerhub
Para o nosso tutorial, o primeiro passo é acessar https://hub.docker.com e criar a sua conta.

# Play with Docker 

Depois que a conta no Docker Hub for criada e confirmada, acessar o nosso laboratório virtual em http://play-with-docker.com/ utilizando as credenciais que você acabou de criar.

# Comandos básicos

`docker pull`

`docker images `

`docker run `

`docker ps`

`docker logs`

`docker exec`

`docker stop ou docker rm -f`

# Let's **containerize** something!

Vamos precisar de um editor de texto no nosso host, então: 

`apk add nano` ou `apk add vim`.

Vamos criar um diretório para nossa aplicação:

`mkdir src && cd src && vim app.py`

*/root/src/app.py*
```python
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello_world():
    return f"<p>Hello, World!</p>"
```

`docker run -it --rm -v /root/src:/aplicacao -p 80:5000 alpine `
- `apk add python3 py3-pip`
- `cd /aplicacao`
- `pip install flask`
- `export FLASK_APP=app`
- `flask run --host=0.0.0.0`

# Variáveis de ambiente 

Vamos modificar a nossa aplicação para que possamos passar uma informação via variáveis de ambiente.

*/root/src/app.py*
```python
from flask import Flask
import os # 1

app = Flask(__name__)
appname = os.getenv('APP_NAME') #2

@app.route("/")
def hello_world():
    return f"<p>Hello, World from {appname}!</p>" #3
```

Vamos criar o arquivo que informa quais bibliotecas do python nossa aplicação precisa.

*/root/src/requirements.txt*
```
flask
```

# Dockerfile
Com o Dockerfile é possível definir todos os passos necessários para que nossa aplicação funcione.

*/root/Dockerfile*
```Dockerfile
FROM alpine

ENV FLASK_APP=app

RUN apk add python3 py3-pip 

COPY src/requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt --no-cache-dir

COPY src /app

EXPOSE 5000

ENTRYPOINT ["flask", "run", "--host=0.0.0.0"]
```
`docker build -t app:0.1 .`

`docker run -d -p 5000:5000 -e APP_NAME=Flask01 app:0.1`

# Publicando uma imagem

`docker login`

`docker image history`

`docker tag app:0.1 grstein/app:0.1`

`docker push`

`docker rm -f grstein/app:0.1`

`docker run -d -p 5001:5000 -e APP_NAME=Flask02 grstein/app:0.1`

# Balanceador de carga 
O NGINX é um proxy reverso que vai nos ajudar a distribuir a carga entre as duas instâncias da nossa aplicação, mas a instância **flask01** vai receber o dobro de requisições por conta da configuração **weight**. Não esqueça de trocar o **x.x.x.x** pelo IP do seu host no laboratório.

`docker push nginx`

*/root/nginx.conf*
```conf
upstream loadbalancer {
server x.x.x.x:5000 weight=2;
server x.x.x.x:5001 weight=1;
}
server {
location / {
proxy_pass http://loadbalancer;
}}
```

`docker run -v ./nginx.conf:/etc/nginx/conf.d/default.conf -p 80:80 nginx`

# Volumes
Existem duas formas de montar arquivos dentro do container: **Named Volume** e **Bind Mount**.

## Named Volume
Cria uma unidade virtual para ser montada dentro do container. Ex:

`docker volume create dados` Cria uma unidade virtual chamada dados.

`docker volume inspect dados` Exibe informações sobre a unidade virtual dados.

`docker run -p 5000:5000 -e APP_NAME=Flask-01 -v dados:/dados grstein/app:0.1` Repare que após o **-v** vem o nome da unidade virtual que criamos.

`docker volume rm dados` Remove a unidade virtual dados.

## Bind Mount
Monta um diretório do host dentro do container. Ex:

`docker run -p 5000:5000 -e APP_NAME=Flask-01 -v /root/src:/app_dev -w /app_dev grstein/app:0.1`

ou 

`docker run -p 5000:5000 -e APP_NAME=Flask-01 -v ./src:/app_dev -w /app_dev grstein/app:0.1`

Repare que logo após o **-v** indicamos um diretório do host.

# Persistência de dados
Como exemplo dos volumes, vamos utilizar o [REDIS|https://redis.io/] para gravar dados e responder a consultas pelas instâncias da nossa aplicação.
Primeiro vamos alterar nossa aplicação:

*/root/src/app.py*
```python
from flask import Flask

import redis #4
import os # 1

redis_cache = redis.Redis(host='redis', port=6379, db=0, password="") #5

app = Flask(__name__)

appname = os.getenv('APP_NAME') #2

@app.route("/")
def hello_world():
    return f"<p>Hello, World from {appname}!</p>" #3

# Comando SET no REDIS #6
@app.route('/set/<string:key>/<string:value>')
def set(key, value):
	if redis_cache.exists(key):
		return f"{appname}: {key} já existe"
	else:
		redis_cache.set(key, value)
		return f"{appname}: registrado no REDIS"

# Comando GET no REDIS #7
@app.route('/get/<string:key>')
def get(key):
	if redis_cache.exists(key):
		return f"{appname}: {redis_cache.get(key)}"
	else:
		return f"{appname}: {key} não existe"
```

Vamos adicionar uma nova biblioteca:

*/root/src/requirements.txt*
```
flask
redis
```
# docker-compose
O docker compose é um programa que define e roda ambientes multi-container, como o nosso. Usa-se um arquivo YAML para descrever o ambiente e, depois disso, é possível subir todos os containers apenas com o comando `docker-compose up`. Em **image:** você poderá mudar o **grstein** que é a referência ao meu repositório no docker hub para o seu username e utilizar a sua imagem.

Vamos criar o arquivo **docker-compose** que definirá nosso ambiente:

*/root/docker-compose*
```Dockerfile
version: '3.8'

services:
  flask01:
    image: grstein/app:0.1
    environment:
      - APP_NAME=Flask01
    expose:
      - 5000

  flask02:
    image: grstein/app:0.1
    environment:
        - APP_NAME=Flask02
    expose:
      - 5000

  redis:
    image: redis:latest
    expose:
      - 6379

  balanceador:
    image: nginx:latest
    ports:
      - 80:80
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
```

Precisaremos alterar as configurações do nginx. Atenção que agora as duas portas serão 5000 pois o docker-compose criará cada instância com o **hostname** igual ao **service** configurado no arquivo YAML:

*/root/nginx.conf*
```conf
upstream loadbalancer {
server flask01:5000 weight=2;
server flask02:5000 weight=1;
}
server {
location / {
proxy_pass http://loadbalancer;
}}
```

`docker-compose up`

# Multi-stage builds

O Build Multi-stage é um método de organização do Dockerfile que minimiza o tamanho final do container e melhora sua performance. É utilizado, geralmente, com aplicações que precisam ser compiladas ou construídas. Uma aplicação em Java, por exemplo, pode ser construída pelo Maven, mas o Mavem em si e tudo que ele baixa, não são necessários em tempo de execução. Desta forma, é possível utilizar uma imagem do Mavem para contruir a aplicação Java e depois copiar os artefatos construídos para outra imagem que possui apenas a JVM. Ex:

Exemplo de Multi-Staged Build para Java:

```Dockerfile
FROM maven AS build
WORKDIR /app
COPY . .
RUN mvn package

FROM tomcat
COPY --from=build /app/target/file.war /usr/local/tomcat/webapps 
```

Exemplo de Multi-Staged Build para Python:

```Dockerfile
## Referência de criação da imagem multi-staged: https://pythonspeed.com/articles/multi-stage-docker-python/

### Imagem do python 3.7 baseada no debian buster com aprox. 1GB
### Utilizada para compilar os requeriments da aplicação
### --user faz com que eles sejam instalados em /root/.local

FROM python:3.7-buster AS compile-image

RUN apt update && apt install -y gettext libpq-dev python-dev libldap2-dev libsasl2-dev python-ldap

COPY src/requirements.txt /app/

RUN cd /app && pip3 install --user -r requirements.txt

### Imagem do python 3.7 baseada no alpine linux com aprox. 175MB
### Apenas o diretório /root/.local é copiado da imagem acima (compile-image)

FROM python:3.7-alpine3.11 AS build-image

ENV PATH=/home/user/.local/bin:$PATH

RUN addgroup -S --gid 500 group && adduser -S -u 500 -h "/home/user" -s /bin/sh user group && chmod 755 "/home/user"

COPY --from=compile-image --chown=user:group /root/.local /home/user/.local
COPY --chown=user:group src/ /app 
COPY --chown=user:group app-init.sh /scripts/app-init.sh

RUN chown -R user:group /scripts && chown -R user:group "/home/user"

WORKDIR /app

USER user

EXPOSE 5000

# ENTRYPOINT ["/bin/sh","/scripts/app-init.sh"]
ENTRYPOINT ["flask", "run", "--host=0.0.0.0"]
```
# Referências

https://www.docker.com/

https://www.docker.com/resources/what-container

https://docs.docker.com/get-started/

https://docs.docker.com/reference/

https://flask.palletsprojects.com/en/2.0.x/quickstart/

https://docs.docker.com/compose/compose-file/
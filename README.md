<h1 align="center">CDC Pipeline — Kafka + Debezium + PostgreSQL + MinIO</h1>

<p align="center">
   Pipeline <b>end-to-end</b> para captura de mudanças (CDC) usando <b>Debezium</b> e <b>Kafka</b>, com replicação para <b>PostgreSQL Sink</b> e persistência em <b>MinIO (S3/Parquet)</b>.
</p>

<p align="center">
   <img src="https://img.shields.io/badge/Kafka-3.x-orange" />
   <img src="https://img.shields.io/badge/Debezium-1.x-blue" />
   <img src="https://img.shields.io/badge/PostgreSQL-13-336791" />
   <img src="https://img.shields.io/badge/MinIO-latest-green" />
   <img src="https://img.shields.io/badge/Docker%20Compose-2.x-lightgrey" />
</p>

<hr/>

<h2>O que este projeto entrega</h2>
<ul>
   <li><b>CDC end-to-end</b> capturando INSERT/UPDATE/DELETE do PostgreSQL via WAL.</li>
   <li><b>Publicação</b> dos eventos em Kafka com gerenciamento de schemas (Schema Registry).</li>
   <li><b>Replicação</b> para PostgreSQL Sink (JDBC Sink Connector) em modo upsert.</li>
   <li><b>Persistência</b> de arquivos Parquet em MinIO através do S3 Sink Connector.</li>
   <li><b>Scripts</b> automatizados para setup, carga inicial, mutações de teste e validação.</li>
</ul>

<hr/>

<h2>Arquitetura (visão geral)</h2>

<pre>
[postgres-source] --(WAL CDC)--> [Debezium Source] --(Kafka + Schema Registry)--> [Kafka Topics]
                                                                                          |                      
                                                                                          |--> [JDBC Sink -> postgres-sink]
                                                                                          |--> [S3 Sink -> MinIO (Parquet)]
</pre>

<hr/>

<h2>Estrutura (trecho relevante)</h2>

<pre>
Arq_Micro_MBA_Eng/
└─ trabalho/
    ├─ connectors/
    │  ├─ debezium-source.json
    │  ├─ jdbc-sink-postgres.json
    │  └─ s3-sink-minio.json
    ├─ scripts/
    │  ├─ setup.sh
    │  ├─ initial_load.py
    │  ├─ mutations.py
    │  └─ validate.sh
    ├─ docker-compose.yml
    └─ requirements.txt
</pre>

<hr/>

<h2>Pré-requisitos</h2>
<ul>
   <li>Docker Desktop (ou Docker Engine) + Docker Compose</li>
   <li>Portas livres: <code>9092</code> (Kafka), <code>8083</code> (Kafka Connect), <code>9000</code> (MinIO), <code>5432/5433</code> (Postgres)</li>
</ul>

<hr/>

<h2>Como subir o ambiente</h2>

<h3>1) Clone o repositório</h3>

<pre><code>git clone https://github.com/rafaeld3v/Arq_Micro_MBA_Eng.git
cd Arq_Micro_MBA_Eng
git fetch --all
git checkout trab_rafael_dante
</code></pre>

<h3>2) Suba os containers</h3>

<p>Com <b>Docker Compose</b>:</p>
<pre><code>cd trabalho
docker-compose up -d
</code></pre>

<h3>3) Instale dependências Python (opcional para scripts)</h3>
<pre><code>pip install -r requirements.txt
</code></pre>

<h3>4) Execute o setup e cargas de teste</h3>

<pre><code>bash scripts/setup.sh         # registra conectores e prepara o ambiente
python scripts/initial_load.py # insere dados iniciais
python scripts/mutations.py    # insere/atualiza/deleta para testar CDC
bash scripts/validate.sh       # valida replicação para sinks
</code></pre>

<hr/>

<h2>Executando o pipeline</h2>

<ol>
   <li>Abra o docker-compose e verifique se todos os serviços estão <code>Up</code>.</li>
   <li>Rode <code>bash scripts/setup.sh</code> (registra conectores).</li>
   <li>Rode <code>python scripts/initial_load.py</code> para inserir dados iniciais.</li>
   <li>Rode <code>python scripts/mutations.py</code> para gerar INSERT/UPDATE/DELETE.</li>
   <li>Cheque com <code>bash scripts/validate.sh</code> se os dados chegaram nos sinks.</li>
</ol>

<hr/>

<h2>Tabela criada (exemplo)</h2>

<ul>
   <li><code>products</code> no banco do sink (ex.: <code>postgres-sink</code>)</li>
</ul>

<p>Exemplo para inspecionar via psql:</p>

<pre><code>docker exec -it postgres-sink psql -U postgres -d sink_db -c "SELECT id, name, price, stock FROM products LIMIT 10;"
</code></pre>

<hr/>

<h2>Troubleshooting rápido</h2>

<ul>
   <li><b>Conector JDBC falhando com erro de tipo</b>: verifique o esquema da tabela no Postgres sink e os tipos enviados pelo Debezium (timestamps/decimals podem precisar de configuração no conector). Habilite <code>schema.evolution</code> se desejar que o conector altere colunas automaticamente.</li>
   <li><b>S3 Sink sem arquivos</b>: verifique parâmetros <code>flush.size</code> e <code>rotate.interval.ms</code> no conector; gere tráfego suficiente no tópico para forçar o flush.</li>
   <li><b>Conector Debezium não captura</b>: confirme que o PostgreSQL fonte está com <code>wal_level=logical</code> e que existe slot de replicação válido.</li>
</ul>

<hr/>

<h2>Tecnologias</h2>

<table>
   <tr><td>Orquestração</td><td>Docker Compose</td></tr>
   <tr><td>Captura CDC</td><td>Debezium (Postgres Source)</td></tr>
   <tr><td>Streaming</td><td>Apache Kafka + Schema Registry</td></tr>
   <tr><td>Sinks</td><td>JDBC Sink (Postgres), S3 Sink (MinIO/Parquet)</td></tr>
   <tr><td>Lang</td><td>Python (scripts)</td></tr>
</table>

<hr/>

<h2>Licença</h2>
<p>Projeto acadêmico — uso educacional.</p>

<p>Desenvolvido por:<br/>
<a href="https://www.linkedin.com/in/rafaeld3v/" target="_blank">Rafael Tavares (LinkedIn)</a> - 2517595<br/>
<a href="https://www.linkedin.com/in/dantedod/" target="_blank">Dante Dantas (LinkedIn)</a> - 2518583</p>
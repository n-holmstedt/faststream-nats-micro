from faststream import FastStream, Logger
from faststream.nats import NatsBroker, NatsMessage
from socket import gethostname
from NatsServiceAPI import NatsServiceAPI
import time
import uuid
import random

broker = NatsBroker("nats://localhost:4222")
app = FastStream(broker)
queue_group = "just_a_string"
version = "0.0.1"

# Create a ServiceAPI object
app.service_api = NatsServiceAPI(
    name=gethostname(),                            # The name of our app/service, for now, our hostname.
    id=str(uuid.uuid4()),                          # Unique id for the specific instance of our service
    version=version,                               # App version
    description="FastStream Service API Class",    # App description
    broker=broker                                  # The FastAPI broker
)

# Generate the ServiceAPI endpoints on startup
@app.on_startup
async def setup():
    app.service_api.add_endpoints()
    # ~/tmp/faststream/nats/bin$ nats micro ls
    # ╭───────────────────────────────────────────────────────────────────────────────────────────────╮
    # │                                       All Micro Services                                      │
    # ├───────────────┬─────────┬──────────────────────────────────────┬──────────────────────────────┤
    # │ Name          │ Version │ ID                                   │ Description                  │
    # ├───────────────┼─────────┼──────────────────────────────────────┼──────────────────────────────┤
    # │ TSELSE3919942 │ 0.0.1   │ 7f71155f-10f4-430b-800d-f173eed53bbf │ FastStream Service API Class │
    # ╰───────────────┴─────────┴──────────────────────────────────────┴──────────────────────────────╯

# Adding a sample public service endpoint will dynamically create NATS Service Framework Endpoints
@broker.subscriber("name.*.test", queue_group)
async def handler(msg: NatsMessage, logger: Logger) -> str:
    processing_time = time.time_ns()
    # Access the endpoint objects to: track amount of requests,
    ep_stats = app.service_api.get_stats_endpoint("name.*.test")
    ep_stats.num_requests += 1
    ep_stats.processing_time += time.time_ns() - processing_time
    ep_stats.average_processing_time = int(ep_stats.processing_time / ep_stats.num_requests)

    #Random error generator
    i = random.randrange(10)
    if i == 9:
        print(i)
        ep_stats.num_errors += 1
    
    return str(msg)

# Another sample service endpoint
@broker.subscriber("other.subject.entirely", queue_group)
async def handler(msg: NatsMessage, logger: Logger) -> str:
    processing_time = time.time_ns()
    logger.info(msg.headers)
    ep_stats = app.service_api.get_stats_endpoint("other.subject.entirely")
    ep_stats.num_requests += 1
    ep_stats.processing_time += time.time_ns() - processing_time
    ep_stats.average_processing_time = int(ep_stats.processing_time / ep_stats.num_requests)
    return str(msg)

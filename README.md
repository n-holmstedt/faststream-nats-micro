# faststream-nats-micro

Needed some kind of project to get started with [FastStream NATS](https://faststream.airt.ai/latest/nats/) so i decided to try implementing the [NATS Service API](https://github.com/nats-io/nats-architecture-and-design/blob/main/adr/ADR-32.md) aka NATS Micro, since i wanted to dig into how that worked aswell. 

The service API is already implemented in the [NATS python client](https://github.com/nats-io/nats.py/tree/main/nats/micro) but since my knowledge of FastStream is pretty shallow, and that it is a platform specific implementation i thought I'd try implementing it separately.

## Usage
Create the broker and add it to  the app. Create an instance of the ServiceAPI and add it to the app. 
```python
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
```
Once added to the app, run ``add_endpoints()`` at startup to add your endpoints to the service api.
```python
@app.on_startup
async def setup():
    app.service_api.add_endpoints()
```
See ``app.py`` for full example.
## Caveats
* This project is made public for insight into faststream, NATS and its micro framework. Its not tested for any production usecases.
* The implementation uses the non-public subscribers of the FastStream broker, which is slightly awkward. Couldn't find any public API for this.
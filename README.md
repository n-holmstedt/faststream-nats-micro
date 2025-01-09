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
Once added to the app, run ``add_endpoints()`` at startup to add your faststream endpoints to the service api.
```python
@app.on_startup
async def setup():
    app.service_api.add_endpoints()
```
See ``app.py`` for full example.

Starting the application, the fastream app should be visible as a nats micro instance. 

```cli
~/code/faststream-nats-micro$ faststream run app:app
2025-01-08 15:15:36,588 INFO     - FastStream app starting...
```
```cli
~/code/faststream-nats-micro$ nats micro ls
╭───────────────────────────────────────────────────────────────────────────────────────────────╮
│                                       All Micro Services                                      │
├───────────────┬─────────┬──────────────────────────────────────┬──────────────────────────────┤
│ Name          │ Version │ ID                                   │ Description                  │
├───────────────┼─────────┼──────────────────────────────────────┼──────────────────────────────┤
│ TSELSE3919942 │ 0.0.1   │ 0dc58018-8dd9-48e1-b270-158f77c45f79 │ FastStream Service API Class │
╰───────────────┴─────────┴──────────────────────────────────────┴──────────────────────────────╯
```
```cli
~/code/faststream-nats-micro$ nats micro info TSELSE3919942
Service Information

          Service: TSELSE3919942 (e0631efd-dca0-4521-8c06-ec2efb8a9528)
      Description: FastStream Service API Class
          Version: 0.0.1

Endpoints:

               Name: test
            Subject: name.*.test
        Queue Group: just_a_string

               Name: entirely
            Subject: other.subject.entirely
        Queue Group: just_a_string

Statistics for 2 Endpoint(s):

  test Endpoint Statistics:

           Requests: 0 in group "just_a_string"
    Processing Time: 0s (average 0s)
            Started: 2025-01-08 15:15:36 (1m33s ago)
             Errors: 0

  entirely Endpoint Statistics:

           Requests: 0 in group "just_a_string"
    Processing Time: 0s (average 0s)
            Started: 2025-01-08 15:15:36 (1m33s ago)
             Errors: 0
```
Trying out the statistics interface in ``app.py`` (with included 10% error simulation):
```cli
~/code/faststream-nats-micro$ nats req name.foo.test 'foobar' --count=100

100 / 100 [==================================================================]    0s
```
```cli
~/code/faststream-nats-micro$ nats micro stats TSELSE3919942
╭──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│                                           TSELSE3919942 Service Statistics                                           │
├──────────────────────────────────────┬──────────┬──────────┬───────────────┬────────┬─────────────────┬──────────────┤
│ ID                                   │ Endpoint │ Requests │ Queue Group   │ Errors │ Processing Time │ Average Time │
├──────────────────────────────────────┼──────────┼──────────┼───────────────┼────────┼─────────────────┼──────────────┤
│ 3cb2fc1d-92ed-43da-aebc-935d84dfc24e │ test     │ 100      │ just_a_string │ 11     │ 1ms             │ 10µs         │
│                                      │ entirely │ 0        │ just_a_string │ 0      │ 0s              │ 0s           │
├──────────────────────────────────────┼──────────┼──────────┼───────────────┼────────┼─────────────────┼──────────────┤
│                                      │          │ 100      │               │ 11     │ 1MS             │ 9ΜS          │
╰──────────────────────────────────────┴──────────┴──────────┴───────────────┴────────┴─────────────────┴─────────────
```

## Caveats
* This project is made public for insight into faststream, NATS and its micro framework. Its not tested for any production usecases.
* The implementation uses the non-public subscribers of the FastStream broker, which is slightly awkward. Couldn't find any public API for this.
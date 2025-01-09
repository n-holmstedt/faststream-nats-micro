
from json import dumps as json_dumps
from dataclasses import dataclass, field
from datetime import datetime, timezone
from faststream.nats import NatsMessage
from faststream import Logger

# [Service API](https://github.com/nats-io/nats-architecture-and-design/blob/main/adr/ADR-32.md)
@dataclass
class NatsServiceAPI:
    name: str
    id: str
    version: str
    metadata: dict = field(default_factory=dict) 
    description: str = ""
    _broker = None
    _subject_endpoints = {"STATS":{}, "INFO":{} }
    _payloads = {"STATS":{}, "INFO":{}, "PING":{}}


    def __str__(self):
        return json_dumps(self.__dict__)

    def __init__(
            self,
            id:str,
            version:str,
            description:str,
            broker:object,
            name:str,
            metadata:dict = None):
        self.name = name
        self.id = id
        self.version = version
        self.description = description
        self.metadata = metadata
        self._broker = broker
        self._payloads = {
            "STATS": StatsAPI(self.name, self.id, self.version, self.metadata),
            "INFO": InfoAPI(self.name, self.id, self.version, self.metadata, self.description),
            "PING": PingAPI(self.name, self.id, self.version, self.metadata)
        }
        self._add_discovery_subjects_to_broker()

    # To be run @startup.
    def add_endpoints(self) -> None:
        # There is no public api for subscribers in the broker.
        for endpoint in self._broker._subscribers.values():
            if endpoint.subject.startswith("$SRV"):
                continue

            endpoint_name = endpoint.description
            if not endpoint_name:
                 endpoint_name = endpoint.subject.split(".")[-1]

            #Create endpoint objects for public manipulation
            self._subject_endpoints["INFO"][endpoint.subject] = InfoEp({
                "name": endpoint_name,
                "subject": endpoint.subject,
                "queue_group": endpoint.queue,
                "metadata": self.metadata
               })
            
            self._subject_endpoints["STATS"][endpoint.subject] = StatsEp({
                "name": endpoint_name,
                "subject": endpoint.subject,
                "queue_group": endpoint.queue,
                "num_requests": 0,
                "num_errors": 0,
                "processing_time": 0,
                "average_processing_time": 0
               })
            
            #Pass stats/info endpoint dict as ref to the payloads.
            self._payloads["STATS"].endpoints.append(
                    self._subject_endpoints["STATS"][endpoint.subject]._ep)
            self._payloads["INFO"].endpoints.append(
                    self._subject_endpoints["INFO"][endpoint.subject]._ep)

    # Get stats endpoint object for a specific subscription
    def get_stats_endpoint(self, subject:str) -> object:
        return self._subject_endpoints["STATS"].get(subject, None)

    # Get info endpoint object for a specific subscription
    def get_info_endpoint(self, subject:str) -> object:
        return self._subject_endpoints["INFO"].get(subject, None)

    # Generate 3x3 NATS subjects based on type[PING|INFO|STATS], service-name and instance id.
    def _generate_discovery_subjects(self):
        discovery_endpoints = []
        for endpoint_type in self._payloads.keys():
            discovery_endpoints.append(f"$SRV.{endpoint_type}")
            discovery_endpoints.append(f"$SRV.{endpoint_type}.{self.name}")
            discovery_endpoints.append(f"$SRV.{endpoint_type}.{self.name}.{self.id}")
        return discovery_endpoints

    # Add NATS Service Framework internal services as broker subscriber
    def _add_discovery_subjects_to_broker(self):
        for subject in self._generate_discovery_subjects():
            sub = self._broker.subscriber(subject)
            sub(self._sevice_framework_handler)

    # Handler for NATS Service Framework internal endpoints 
    async def _sevice_framework_handler(self, msg: NatsMessage, logger: Logger):
        raw: Msg = msg.raw_message
        msg_type = raw.subject.split(".")[1] #PING|INFO|STATS
        logger.debug(raw)
        return str(self._payloads[msg_type])

@dataclass
class StatsAPI(NatsServiceAPI):
    started: str = str(datetime.now(timezone.utc).isoformat())
    endpoints: list = field(default_factory=list) 
    type: str = "io.nats.micro.v1.stats_response"

@dataclass
class PingAPI(NatsServiceAPI):
    type: str = "io.nats.micro.v1.ping"

@dataclass
class InfoAPI(NatsServiceAPI):
    endpoints: list = field(default_factory=list)
    type: str = "io.nats.micro.v1.info_response"

@dataclass
class InfoEp:
    _ep = {}
    def __init__(self, ep_dict):
        self._ep = ep_dict

    def __str__(self):
        return json_dumps(self.__dict__)

    @property
    def name(self) -> str:
        return self._ep["name"] 

    @property
    def subject(self) -> str:
        return self._ep["subject"]  
    
    @property
    def queue_group(self) -> str:
        return self._ep["queue_group"]
    
    @property
    def metadata(self) -> str:
        return self._ep["metadata"]
    
    @metadata.setter
    def metadata(self, metadata:dict) -> None:
        self._ep["metadata"] = metadata

    def __str__(self):
        return json_dumps(self.__dict__)

@dataclass
class StatsEp(InfoEp):
    def __init__(self, ep_dict):
        super().__init__(ep_dict)
    
    @property
    def num_requests(self) -> int:
        return self._ep["num_requests"]
    
    @num_requests.setter
    def num_requests(self, i) -> None:
        self._ep["num_requests"] = i

    @property
    def num_errors(self) -> int:
        return self._ep["num_errors"]

    @num_errors.setter
    def num_errors(self, i) -> None:
        self._ep["num_errors"] = i
    
    @property
    def processing_time(self) -> str:
        return self._ep["processing_time"]

    @processing_time.setter
    def processing_time(self, i) -> None:
        self._ep["processing_time"] = i

    @property
    def average_processing_time(self) -> str:
        return self._ep["average_processing_time"]
    
    @average_processing_time.setter
    def average_processing_time(self, i) -> None:
        self._ep["average_processing_time"] = i

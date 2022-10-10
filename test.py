##
from dataclasses import KW_ONLY, field, dataclass
from dataclasses_json import dataclass_json, config


@dataclass_json
@dataclass
class TestObject:
    id: int

@dataclass_json
@dataclass
class Test2:
    _:KW_ONLY
    test:TestObject = None

    # def __post_init__(self):
    #     if self.test is not None:
    #         self.test = TestObject.from_json(self.test)


print(Test2.from_json('{"test":{"id":10}}').test.id)




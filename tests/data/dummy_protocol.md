# Dummy Protocol

## Description

A dummy protocol for testing purposes

## Specification

```yaml
name: dummy_protocol
author: your_name
version: 1.0.0
description: A dummy protocol for testing.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
protocol_specification_id: your_name/dummy_protocol:1.0.0
speech_acts:
  request:
    template: pt:str
    params: pt:dict[pt:str, pt:str]
  response:
    result: pt:dict[pt:str, pt:str]
  error:
    error_code: ct:ErrorCode
    error_msg: pt:str
...
---
ct:ErrorCode: |
  enum ErrorCodeEnum {
      INVALID_REQUEST = 0;
      INTERNAL_ERROR = 1;
    }
  ErrorCodeEnum error_code = 1;
...
---
initiation:
- request
reply:
  request: [ response, error ]
  response: [ ]
  error: [ ]
termination: [ response, error ]
roles: { client, server }
end_states: [ response, error ]
keep_terminal_state_dialogues: true
```

## Links

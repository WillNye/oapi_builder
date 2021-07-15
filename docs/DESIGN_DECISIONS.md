# Design Decisions

## Objectives
The primary purposes of `oapi_builder` are as followed:
* Make the OAPI structure more explicit by representing schema objects as dataclasses 
* Create a process that makes it easy to extend or create an OAPI doc in Python from scratch
* Lower the barrier to entry for creating an OAPI doc

## Design Considerations
The following considerations needed to be made for `oapi_builder` to be viable
* When setting nested schema objects; instance attributes must accept either a class instance or, the low level dict as a value 





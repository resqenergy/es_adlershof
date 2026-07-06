
Turn functionality in @read_datapacakge_from_s3.py into a class by inheriting from Package class of frictionless.

if path to datapacakge.json uses s3:// prefix, an AWSControl shall be used. otherwise default package behaviour shall be used (aka reading and writing resources from local filesystem)

Following functions should be added to class:
- read a resource from package by resource name - regard if S3 storage is used or local filesystem
- write a resource to package by resource name - regard if S3 storage is used or local filesystem, this shall automatically add resource to package datapackage.json

if resource is ".csv" or ".txt" file return a dataframe, otherwise a dict (in case of .json or .yaml)

# Architecture

QuickDrop stores only metadata in the relational database. Uploaded bytes are stored under random internal object names; public tokens never map directly to a storage path.

At request time Flask validates status and UTC expiry before returning metadata or bytes. The scheduled cleanup job is a physical-storage cleanup mechanism, not the access-control mechanism. This guarantees an expired share remains inaccessible even if a timer invocation is delayed.

Production uses PostgreSQL through SQLAlchemy and Azure Blob Storage through the storage service interface. The local implementations exist solely to make development and tests inexpensive.

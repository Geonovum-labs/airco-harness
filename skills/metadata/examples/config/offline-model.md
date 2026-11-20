# Trees metadata model

Version: `1`. This fictional model describes **metadata**, not tree objects. It defines the roles *listing*, *subject*, *representation*, *access interface* and *declared specification*.

In the trees catalog, map `dcat:CatalogRecord` to *listing*, `foaf:primaryTopic` to its *subject*, `dcat:Distribution` to *representation*, and `dcat:DataService` to *access interface*. Read a `dct:conformsTo` assertion from that access interface as a *declared specification*. Keep the original predicates. For terms this model does not cover, cite the source vocabulary without inventing a mapping.

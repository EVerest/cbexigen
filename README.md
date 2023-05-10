# cbExiGen - The V2GTP EXI codec generator

cbExiGen is a code generator which creates the codec library **cbV2G** for
encoding and decoding messages using the Vehicle To Grid Transport Protocol
(V2GTP). It is capable of processing XML schemas as defined in the standards
DIN 70121, ISO 15118-2 and ISO 15118-20, and derivates of these. It creates
a library capable of encoding and decoding the complete EXI message set of
the defined protocols.

---
## :exclamation: Call for ISO 15118-20 EXI streams :exclamation:

You would greatly suppport this project if you are able to provide real-life
EXI streams of ISO 15118-20 messages. We need these to validate the quality
of the code. Any streams would be appreciated. Formats can be binary or
hex-represented V2GTP messages, or just their EXI payload, or traffic
captures (PCAP or PCAPNG). If possible, provide the corresponding expected
content (e.g. as XML, JSON, or just a list of fields and values).

Please get in touch with the authors, or
[open a GitHub issue](https://github.com/EVerest/cbexigen/issues/new).

Thank you!

---

## What

V2GTP is a protocol for "vehicle to grid" communication. It is used for
control of power flow in charging electrical vehicles (EVs), for the
communication between EV and EVSE (electical vehicle supply equipment, i.e.
charging station).

The protocol is originally defined in the global standard ISO 15118. Its
popular implementations are
[DIN 70121](https://www.beuth.de/en/technical-rule/din-spec-70121/224350045),
[ISO 15118-2](https://www.iso.org/standard/55366.html), and
[ISO 15118-20](https://www.iso.org/standard/77845.html).

The protocol is XML based, with the messages representable as XML, strictly
defined using XML schemas. The message transfer uses EXI ([Efficient XML
Interchange](http://www.w3.org/TR/exi/)), a compact binary representation of
XML.

The codec is not implemented directly, but using this code generator,
because the standards are evolving, yet share common ground. A code
generator allows modifying a schema e.g. to implement experimental
extensions, and allows creating a codec for future standard variants. The
generator also aids in optimizing the code, by improving the EXI grammar
evaluation, and by implementing configurations for limited protocol coverage
for reduced code size, without the need to manually modify many places
within the complete library.

The code generator takes the standards' XML schema files as input, analyzes
them, and creates the appropriate codec representation.

This codec created by this code generator is designed to take a data
representation of the message data - e.g. as structs or classes - and
convert it to the binary EXI message representation, and vice versa.

The codec only abstacts the data representation. It does *not* enforce
message order, message content (beyond what the XML schemas mandate) or
other higher level requirements.

The code generator currently targets creation of C code, but can be expanded
to support codecs in other programming languages.

## Requirements

The code generator requires Python 3.7. Furthermore, it requires the Python
module [xmlschema](https://pypi.org/project/xmlschema/) and its dependencies,
especially [jinja2](https://pypi.org/project/Jinja2/). See `requirements.txt`
for precise details.

In order to be able to produce a codec, the standard's XML schema files are
required. These cannot be distributed with the code generator. They are
available within the actual standard documents, partly distributed
separately by the ISO, and also available openly from other sources.

## Configuration

See the configuration files under `src/config*.py`. They include the paths
to the respective schema files, and also define output directories. They
also allow for specifying file and namespace prefixes, in case of creating a
codec which covers several of the named standards.

By inclusion or omission of certain schema files, features of the respective
standards can be included or omitted (e.g. ACDP or WPT from ISO 15118-20).

The default configuration `src/config.py` is set up to build a codec for
both DIN 70121, ISO 15118-2 and ISO 15118-20, as well as appHandshake and
top-level V2GTP, with all their respective features. It uses schema files
in `src/input/schemas/`. It outputs the codec to `src/output/c/`, creates
logs in `src/output/log/`, and uses the prefixes `appHandshake`, `v2gtp`,
`din`, `iso-2` and `common` for the respective codec folders, and similar
prefixes for functions and data types.

## Running the code generator

If the required Python dependencies are not already installed, run
```
$ python -m pip install -r requirements.txt
```
to install them.

To generate the codec, run
```
$ python src/main.py
```

If you have your own config, instead run
```
$ python src/main.py --config_file config_custom.py
```
The config file name should be an absolute path, or relative to the src/
directory.

Be sure to use your appropriate Python 3 (>= 3.7) interpreter.

## License

The code generator and the resulting codec are licensed under the Apache
License Version 2.0.

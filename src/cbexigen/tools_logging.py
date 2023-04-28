# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2023 chargebyte GmbH
# Copyright (c) 2022 - 2023 Contributors to EVerest

""" Logging tools for the Exi Codegenerator """
import logging
from pathlib import Path
from cbexigen.elementData import Particle, ElementData
from cbexigen.tools_config import CONFIG_ARGS


''' Log tools '''


def log_init_logger(logger_name, filename, level=logging.INFO, mode='w'):
    logfile = Path(CONFIG_ARGS['log_dir'], filename).resolve()
    file_hd = logging.FileHandler(logfile, mode)

    file_fm = logging.Formatter('%(levelname)s:%(name)s:  %(message)s')
    file_hd.setFormatter(file_fm)

    log = logging.getLogger(logger_name)
    log.setLevel(level)
    log.addHandler(file_hd)


def log_write_logger(logger_name, message):
    logging.getLogger(logger_name).info(message)


def log_deinit_logger(logger_name):
    log = logging.Logger.manager.loggerDict.get(logger_name)
    if log is not None:
        hnd = log.handlers[0]
        if hnd:
            hnd.close()


def log_exists_logger(logger_name):
    log = logging.Logger.manager.loggerDict.get(logger_name)

    return log is not None


def log_init(file_name):
    logfile = Path(CONFIG_ARGS['log_dir'], file_name).resolve()
    logging.basicConfig(filename=logfile, filemode="w", level=logging.INFO)

    log_init_logger('error', 'error_log.txt', logging.ERROR)


def log_write(message):
    logging.info(message)


def log_write_error(message):
    logging.getLogger('error').error(message)


def log_write_dict(name, elem_dict):
    indent = "            "

    message = name + "\n"
    for elem, value in sorted(elem_dict.items()):
        message += indent + elem + ": " + str(value) + "\n"

    logging.info(message)


def log_write_element_pos_data(element: ElementData):
    message = "   name / type short:   " + element.name_short + " / " + element.type_short + \
              " (" + str(element.level) + ", " + str(element.count) + ")"
    logging.info(message)


def log_write_particle(particle: Particle):
    indent = "            "

    message = "PARTICLE\n"
    # full qualified name
    message += indent + "name:\t\t\t\t" + particle.name + "\n"

    # type name, base
    message += indent + "type:\t\t\t\t" + particle.type + "\n"
    message += indent + "type short:\t\t\t" + particle.type_short + "\n"
    if particle.base_type:
        message += indent + "base type:\t\t\t" + particle.base_type + "\n"

    # other info
    message += indent + "min/max occurs:\t\t" + str(particle.min_occurs) + ", " + str(particle.max_occurs) + "\n"
    message += indent + "min/max length:\t\t" + str(particle.min_length) + ", " + str(particle.max_length) + "\n"
    message += indent + "min/max value:\t\t" + str(particle.min_value) + ", " + str(particle.max_value) + "\n"
    if particle.bit_count_for_coding:
        message += indent + "bits to encode:\t\t" + str(particle.bit_count_for_coding) + "\n"
    message += indent + "abstract:\t\t\t" + str(particle.abstract) + "\n"
    message += indent + "complex:\t\t\t" + str(particle.is_complex) + "\n"
    message += indent + "substitute:\t\t\t" + str(particle.is_substitute)

    logging.info(message)


def log_write_element(element: ElementData):
    indent = "            "

    message = "ELEMENT\n"
    # full qualified name
    message += indent + "name:\t\t\t\t" + element.name + "\n"
    message += indent + "name short:\t\t\t" + element.name_short + "\n"
    message += indent + "level:\t\t\t\t" + str(element.level) + "\n"
    message += indent + "count:\t\t\t\t" + str(element.count) + "\n"

    # definition: simple, complex
    message += indent + "type definition:\t" + element.type_definition + "\n"

    # type name, base
    message += indent + "type:\t\t\t\t" + element.type + "\n"
    message += indent + "type short:\t\t\t" + element.type_short + "\n"
    if element.base_type:
        message += indent + "base type:\t\t\t" + element.base_type + "\n"

    # content type: element only
    if element.content_type:
        message += indent + "content type:\t\t" + element.content_type + "\n"

    # restriction
    if element.derivation:
        message += indent + "derivation:\t\t\t" + element.derivation + "\n"

    # other info
    if element.type_id:
        message += indent + "type id:\t\t\t" + element.type_id + "\n"
    message += indent + "final:\t\t\t\t" + str(element.final) + "\n"
    message += indent + "abstract:\t\t\t" + str(element.abstract)

    logging.info(message)

    # list of particles
    for particle in element.particles:
        log_write_particle(particle)

    log_write("----------")


def msg_write(message, blank_line_before=False):
    print(message)

    if blank_line_before:
        log_write('')
    log_write(message)

# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2023 chargebyte GmbH
# Copyright (c) 2022 - 2023 Contributors to EVerest

""" Generator tools for the Exi Codegenerator """
import os
from pathlib import Path
from xmlschema.extras.codegen import Environment, FileSystemLoader
from v2g_exi_codec_gen import tools
from v2g_exi_codec_gen.tools_config import CONFIG_ARGS
from v2g_exi_codec_gen.elementData import Particle, ElementData


''' common generator tools '''


__GENERATOR = None


def get_generator():
    global __GENERATOR

    if __GENERATOR is None:
        template_subdirs = ['', 'decoder', 'encoder']
        template_dirs = [Path(os.path.join(CONFIG_ARGS['template_dir'], subdir)) for subdir in template_subdirs]
        __GENERATOR = Environment(loader=FileSystemLoader(template_dirs))

    return __GENERATOR


def get_includes_content(config_dict):
    temp = get_generator().get_template('BaseInclude.ctc')
    result = temp.render(std_lib_items=config_dict['include_std_lib'], elements=config_dict['include_other'])

    return tools.adjust_string_start_end(result)


def get_particle_type(particle: Particle):
    result = particle.type_short

    if particle.base_type != '':
        if str.casefold(particle.base_type) == 'anyuri':
            result = 'uri'
        if str.casefold(particle.base_type) == 'string':
            if not particle.is_enum:
                result = 'string'
        elif str.casefold(particle.base_type) == 'base64binary' or str.casefold(particle.base_type) == 'hexbinary':
            result = 'binary'
    else:
        if str.casefold(particle.type_short) == 'anyuri':
            result = 'uri'
        if str.casefold(particle.type_short) == 'string':
            result = 'string'
        elif str.casefold(particle.type_short) == 'base64binary' or str.casefold(
                particle.type_short) == 'hexbinary':
            result = 'binary'

    return result


def get_particle_from_element_by_name(name, sequence, element: ElementData):
    result = None

    occurs = 1
    for item in element.particles:
        if name == item.name:
            if sequence == occurs:
                result = item
                break
            else:
                occurs += 1

    return result


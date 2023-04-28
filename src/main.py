# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 - 2023 chargebyte GmbH
# Copyright (c) 2022 - 2023 Contributors to EVerest

import sys
import argparse
from pathlib import Path

import cbexigen.tools_config as conf
from cbexigen.tools_logging import log_init
from cbexigen import FileGenerator as Generator


def analyze_schema(argv):
    parser = argparse.ArgumentParser(description="Usage of exi codec generator")
    parser.add_argument("--config_file", type=Path, default="config.py",
                        help="Specifies the generator configuration parameter file")
    args = parser.parse_args(argv[1:])
    config = vars(args)

    conf.CONFIG_ARGS['program_dir'] = Path(__file__).parent.resolve()
    conf.CONFIG_ARGS['config_file'] = config['config_file']
    if not conf.check_config_file():
        print('Config file does not exist.')
        exit(1)

    config_module = conf.get_config_module()
    conf.set_config_arg_from_config_file('template_dir', config_module.template_dir)
    conf.set_config_arg_from_config_file('output_dir', config_module.output_dir)
    conf.set_config_arg_from_config_file('schema_base_dir', config_module.schema_base_dir)
    conf.set_config_arg_from_config_file('log_dir', config_module.log_dir)
    conf.process_config_parameters()

    if not conf.check_config_parameters():
        print('Error in config file.')
        exit(2)

    log_init(config_module.log_file_name)

    gen = Generator.FileGenerator()
    gen.generate_files()


if __name__ == '__main__':
    analyze_schema(sys.argv)

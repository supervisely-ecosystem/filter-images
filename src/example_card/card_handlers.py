from fastapi import Depends

import supervisely
from supervisely import logger


def example_route(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    logger.info(f"{state=}")

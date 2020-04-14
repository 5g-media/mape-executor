class ScalingGroupNotFound(Exception):
    """The scaling group of the ns has not defined in the descriptor."""
    pass


class VnfdUnexpectedStatusCode(Exception):
    """The status code of the nsr details is not expected"""
    pass


class VnfScaleNotCompleted(Exception):
    """The status code of the nsr details is not expected"""
    pass


class NsDescriptorNotFound(Exception):
    """The ns descriptor not found"""
    pass


class NsInstantiationNotCompleted(Exception):
    """The instantiation of the NS failed"""
    pass


class NsTerminationNotCompleted(Exception):
    """The instantiation of the NS failed"""
    pass


class vCacheConfigurationFailed(Exception):
    """The day 1/2 configuration of vCache failed"""
    pass


class VdnsConfigurationFailed(Exception):
    """The configuration of vDNS failed"""
    pass


class TranscoderProfileUpdateFailed(Exception):
    """The change of the vtranscoder profile failed"""
    pass


class TranscoderPlacementFailed(Exception):
    """The placement of the vtranscoder failed"""
    pass


class CompressionEngineConfigurationFailed(Exception):
    """The change of the vCE failed"""
    pass


class TranscoderSpectatorsQualityConfigurationFailed(Exception):
    """The change of the spectators qualities failed"""
    pass


class InvalidTranscoderSpectatorsQualities(Exception):
    """The structure of the spectators qualities is not valid"""
    pass

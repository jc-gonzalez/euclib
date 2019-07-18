"""
Main entry into the library
"""
import os, sys
sys.path.insert(1, os.path.dirname(os.path.dirname(__file__)))
del os, sys

def init_param_sampleprovider():
    import pyares.parameter_sample_provider as psp
    return psp.ParameterSampleProvider()


def init_param_jobresultretriever():
    import pyares.parameter_job_result_retriever as pjrr
    return pjrr.ParameterJobResultRetriever()


def init_aresjob(**kwargs):
    import pyares.ares_job as aj
    return aj.AresJob(**kwargs)


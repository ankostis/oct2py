"""
.. module:: _matread
   :synopsis: Read Python values from a MAT file made by Octave.
              Strives to preserve both value and type in transit.

.. moduleauthor:: Steven Silvester <steven.silvester@ieee.org>

"""
import numpy as np
from scipy.io import loadmat
from ._utils import Struct, _create_file, _register_del


class MatRead(object):
    """Read Python values from a MAT file made by Octave.

    Strives to preserve both value and type in transit.

    """
    def __init__(self):
        """Initialize our output file and register it for deletion
        """
        self.out_file = _create_file('save', 'mat')
        _register_del(self.out_file)

    def setup(self, nout, names=None):
        """
        Generate the argout list and the Octave save command.

        Parameters
        ----------
        nout : int
            Number of output arguments required.
        names : array-like, optional
            Variable names to use.

        Returns
        -------
        out : tuple (list, str)
            List of variable names, Octave "save" command line

        """
        argout_list = []
        for i in range(nout):
            if names:
                argout_list.append(names.pop(0))
            else:
                argout_list.append("%s__" % chr(i + 97))
        save_line = 'save "-v6" "%s" "%s"' % (self.out_file,
                                                '" "'.join(argout_list))
        return argout_list, save_line

    def extract_file(self, argout_list):
        """
        Extract the variables in argout_list from the M file

        Parameters
        ----------
        argout_list : array-like
            List of variables to extract from the file

        Returns
        -------
        out : object or tuple
            Variable or tuple of variables extracted.

        """
        data = loadmat(self.out_file)
        outputs = []
        for arg in argout_list:
            val = data[arg]
            val = self._get_data(val)
            outputs.append(val)
        if len(outputs) > 1:
            return tuple(outputs)
        else:
            return outputs[0]

    def _get_data(self, val):
        '''Extract the data from the incoming value
        '''
        # check for objects
        if "'|O" in str(val.dtype):
            data = Struct()
            for key in val.dtype.fields.keys():
                data[key] = self._get_data(val[key][0])
            return data
        # handle cell arrays
        if val.dtype == np.object:
            if val.size == 1:
                val = val[0]
                if "'|O" in str(val.dtype):
                    val = self._get_data(val)
                if val.size == 1:
                    val = val.flatten()[0]
        if val.dtype == np.object:
            if len(val.shape) > 2:
                val = val.T
                val = np.array([self._get_data(val[i].T)
                                for i in range(val.shape[0])])
            if len(val.shape) > 1:
                if len(val.shape) == 2:
                    val = val.T
                try:
                    return val.astype(val[0][0].dtype)
                except ValueError:
                    for row in range(val.shape[0]):
                        for i in range(val[row].size):
                            if not np.isscalar(val[row][i]):
                                val[row][i] = val[row][i][0]
            else:
                val = np.array([self._get_data(val[i]) for i in range(val.size)])
            if len(val.shape) == 1 or val.shape[0] == 1 or val.shape[1] == 1:
                val = val.flatten()
            val = val.tolist()
        elif val.size == 1:
            val = val.flatten()[0]
        return val
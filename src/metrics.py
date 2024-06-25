import numpy as np

def wasserstein(mu1, var1, mu2, var2):
    return np.sqrt(
        ( mu1 - mu2 )**2 + ( np.sqrt(var1) - np.sqrt(var2) )**2
    )

def wasserstein_matrix(mu1, var1, mu2, var2):
    #print( np.trace( var1 ), np.trace( var2 ), np.trace(- 2 * np.transpose( np.transpose(var2) @ var1 @ np.transpose(var2) ) ) )
    return np.sqrt(
        np.linalg.norm( mu1.flatten() - mu2.flatten() )**2 + np.sum(
            var1 + var2 - 2 * np.sqrt( var2 * var1  )
        )
    )

def kullback_leibler(mu1, var1, mu2, var2):
    return 0.5 * (
        var1 / var2 + (mu1 - mu2)**2 / var2 - 1 + 2 * np.log( np.sqrt(var2 / var1) )
    )

def kullback_leibler_matrix(mu1, var1, mu2, var2):
    # KL is additive for independent distributions
    return np.sum( kullback_leibler(mu1, var1, mu2, var2) )
try:
    import scipy.optimize
    print("scipy.optimize OK")
except ImportError as e:
    print("no scipy:", e)

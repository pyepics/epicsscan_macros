## XRF commands
def expose(t=60):
    open_shutter()
    t0 = time.time()
    tend = t0 + t
    while time.time() < tend:
        sleep(1)
    print("Done exposed for %.3f sec" % (time.time()-t0))
    close_shutter()

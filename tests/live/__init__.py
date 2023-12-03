"""
Collection of "live" Tests.

All tests that require an Internet connection go under here. Tests outside of
this package should have any web request attempts mocked.  The purpose of these
tests should be to verify that all of the modules are still working with the
current state of the sites that they purport to scrape.

If the sites change formatting, themes, backend systems or even switch domains,
this should be a way to easily verify what is and isn't currently working,
especially for modules that see less frequent use.

All tests should be tagged as 'live' via pytest's marking system::

    @pytest.mark.live
    class ExampleUnitTest(unittest.TestCase):
        pass


    @pytest.mark.live
    def test_something():
        pass

"""

import os

from conans import AutoToolsBuildEnvironment, ConanFile, RunEnvironment, tools


class AreaDetector(ConanFile):
    name = "areadetector"
    version = "3.5"
    license = ""
    _source = "/Users/brambilla/work/epics/areaDetector"
    description = ""
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=False"
    generators = "gcc"
    requires = 'epics/3.16.1-4.6.0-dm6@ess-dmsc/stable', 're2c/0.1@devel/epics', 'synapps/0.1@devel/epics'

    def get_epics_info(self):
        epics_base = self.deps_cpp_info["epics"].rootpath.replace('/package/', '/build/')

        epics_version = [folder for folder in os.listdir(path=epics_base) if folder.startswith('base-')]
        if epics_version:
            epics_base += '/' + epics_version[0]
            epics_version = epics_version[0].split('-')[1]
            return epics_base, epics_version
        return ('', '')

    def get_module_info(self, modulename):
        result = None
        try:
            result = self.deps_cpp_info[modulename]
        except Exception as e:
            print(e)
        return result

    # replace EPICS paths
    def _replace_epics_base(self):
        epics_base, _ = self.get_epics_info()
        tools.replace_in_file("synApps/support/configure/RELEASE",
                              "SUPPORT=/home/oxygen40/KLANG/Documents/synApps/support",
                              "SUPPORT=" + os.getcwd() + "/synApps/support")
        tools.replace_in_file("synApps/support/configure/RELEASE", "EPICS_BASE=/APSshare/epics/base-3.15.5",
                              "EPICS_BASE=" + epics_base)

    def _set_extra_options(self):
        tools.replace_in_file("synApps/support/configure/CONFIG_SITE", "LINUX_USB_INSTALLED = YES",
                              "LINUX_USB_INSTALLED = NO")
        tools.replace_in_file("synApps/support/configure/CONFIG_SITE", "LINUX_NET_INSTALLED = YES",
                              "LINUX_NET_INSTALLED = NO")

    # deselect unnecessary modules
    def _comment_unwanted_modules(self):
        for module in self.no_modules:
            tools.replace_in_file("synApps/support/configure/RELEASE", module, "# " + module)

    # create a list with the modules that will be built
    def _list_wanted_modules(self, path='synApps/support'):
        prefix = '=$(SUPPORT)/'
        modules = []
        with open(os.path.join(path, 'configure/RELEASE')) as f:
            for line in f:
                if prefix in line and line[0] != '#':
                    modules.append(os.path.basename(line.rstrip()))
        return modules

    def source(self):
        print(self._source)
        self.run('cp -r %r .'%self._source+'/areaDetector')

    def build(self):

        self._replace_epics_base()
        self._set_extra_options()

        autotools = AutoToolsBuildEnvironment(self)
        env_build = RunEnvironment(self)

        # propagate changes through modules
        with tools.chdir('synApps/support'):
            autotools.make(target='release', vars=env_build.vars)

        self._comment_unwanted_modules()
        self.modules = self._list_wanted_modules()

        with tools.chdir('synApps/support'):
            autotools.make(vars=env_build.vars)

    def package(self):

        if tools.os_info.is_linux:
            arch = "linux-x86_64"
        elif tools.os_info.is_macos:
            arch = "darwin-x86"

        for module in self._list_wanted_modules(
                '/Users/brambilla/.conan/data/synapps/0.1/devel/epics/build/4ec342c7155e8f6625f44c01898a08bd8fd5d8f3/synApps/support'):
            path = os.path.join('synApps/support', module, 'lib', arch)
            if os.path.isdir(path):
                self.copy("*.a", dst="lib", src=path, keep_path=False)
                self.copy("*.so", dst="lib", src=path, keep_path=False)
                self.copy("*.dylib", dst="lib", src=path, keep_path=False)
            path = os.path.join('synApps/support', module, 'include')
            if os.path.isdir(path):
                self.copy("*.h", dst="include", src=path, keep_path=False)

    def package_info(self):
        self.cpp_info.libs = self.collect_libs()
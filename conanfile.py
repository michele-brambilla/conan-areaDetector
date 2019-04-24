import os
import shutil

from conans import ConanFile, tools


class AreaDetector(ConanFile):
    name = "areadetector"
    version = "3.5"
    license = ""
    url = "https://github.com/areaDetector/areaDetector.git"
    description = ""
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=False"
    generators = "gcc"
    requires = 'epics/3.16.1-4.6.0-dm6@ess-dmsc/stable', 're2c/0.1@devel/epics', 'synapps/0.1@devel/epics'

    def get_epics_info(self):
        epics_base = self.deps_cpp_info["epics"].rootpath.replace('/package/',
                                                                  '/build/')

        epics_version = [folder for folder in os.listdir(path=epics_base) if
                         folder.startswith('base-')]
        if epics_version:
            epics_base += '/' + epics_version[0]
            epics_version = epics_version[0].split('-')[1]
            return epics_base, epics_version
        return ('', '')

    def get_pva(self):
        epics_base = self.deps_cpp_info["epics"].rootpath.replace('/package/',
                                                                  '/build/')

        pva = [folder for folder in os.listdir(path=epics_base) if
                         folder.startswith('EPICS-CPP-')]

        if pva:
            return os.path.join(epics_base, pva[0])
        return ""

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
        tools.replace_in_file("synApps/support/configure/RELEASE",
                              "EPICS_BASE=/APSshare/epics/base-3.15.5",
                              "EPICS_BASE=" + epics_base)

    def _set_extra_options(self):
        tools.replace_in_file("synApps/support/configure/CONFIG_SITE",
                              "LINUX_USB_INSTALLED = YES",
                              "LINUX_USB_INSTALLED = NO")
        tools.replace_in_file("synApps/support/configure/CONFIG_SITE",
                              "LINUX_NET_INSTALLED = YES",
                              "LINUX_NET_INSTALLED = NO")

    # deselect unnecessary modules
    def _comment_unwanted_modules(self):
        for module in self.no_modules:
            tools.replace_in_file("synApps/support/configure/RELEASE", module,
                                  "# " + module)

    # create a list with the modules that will be built
    def _list_wanted_modules(self, path='synApps/support'):
        prefix = '=$(SUPPORT)/'
        modules = []
        with open(os.path.join(path, 'configure/RELEASE')) as f:
            for line in f:
                if prefix in line and line[0] != '#':
                    modules.append(os.path.basename(line.rstrip()))
        return modules

    def _replace_release_support(self, support):
        source = os.path.join("configure", "RELEASE_SUPPORT.local")
        orig = "SUPPORT=/corvette/home/epics/devel"
        edit = "SUPPORT=" + support
        tools.replace_in_file(source, orig, edit)

    def _replace_release_libs(self, support):
        source = os.path.join("configure", "RELEASE_LIBS.local")

        orig = "ASYN=$(SUPPORT)/asyn-4-35"
        edit = [x for x in os.listdir(support) if "asyn" in x][0]
        tools.replace_in_file(source, orig, "ASYN=$(SUPPORT)/"+edit)

        orig = "AREA_DETECTOR=$(SUPPORT)/areaDetector-3-5"
        edit = [x for x in os.listdir(support) if "areaDetector" in x][0]
        tools.replace_in_file(source, orig, "AREA_DETECTOR=$(SUPPORT)/"+edit)

        orig = "EPICS_BASE=/corvette/usr/local/epics-devel/base-7.0.2"
        edit = "EPICS_BASE="+self.get_epics_info()[0]
        tools.replace_in_file(source, orig, edit)

        orig = "#PVA=/corvette/usr/local/epics-devel/epicsV4/EPICS-CPP-4.6.0"
        edit = "PVA="+self.get_pva()
        tools.replace_in_file(source, orig, edit)

        tools.replace_in_file(source, "#PVCOMMON", "PVCOMMON")
        tools.replace_in_file(source, "#PVACCESS", "PVACCESS")
        tools.replace_in_file(source, "#PVDATA", "PVDATA")
        tools.replace_in_file(source, "#PVDATABASE", "PVDATABASE")
        tools.replace_in_file(source, "#NORMATIVETYPES", "NORMATIVETYPES")


    def _add_linux_config(self):
        for f in ['RELEASE', 'RELEASE_SUPPORT', 'RELEASE_LIBS',
                  'RELEASE_PRODS', 'CONFIG_SITE']:
            shutil.copyfile(
                os.path.join("configure", 'EXAMPLE_' + f + '.local'),
                os.path.join("configure", f + '.local')
            )

        if self.options.shared:
            shared_option_sub = "STATIC_BUILD = NO\nSHARED_LIBRARIES = YES"
        else:
            shared_option_sub = "STATIC_BUILD = YES\nSHARED_LIBRARIES = NO"

        support = os.path.join(self.deps_cpp_info[
            "synapps"].build_paths[0].replace('/package/', '/build/'),
                               'synApps', 'support')
        # edit RELEASE_SUPPORT.local
        self._replace_release_support(support)

        # edit RELEASE_LIBS.local
        self._replace_release_libs(support)


        # tools.replace_in_file(
        #     os.path.join(EPICS_BASE_DIR, "configure", "CONFIG_SITE.local"),
        #     "<static_or_shared>",
        #     shared_option_sub
        # )
        #
        # tools.replace_in_file(
        #     os.path.join(EPICS_BASE_DIR, "configure", "os",
        #                  "CONFIG_SITE.Common.linux-x86_64"),
        #     "COMMANDLINE_LIBRARY = READLINE",
        #     "COMMANDLINE_LIBRARY = EPICS"
        # )

    def source(self):
        git = tools.Git()
        git.clone(self.url)

    def build(self):

        if tools.os_info.is_linux:
            self._add_linux_config()
            # elif tools.os_info.is_macos:
            #     self._add_darwin_config()
            # elif tools.os_info.is_windows:
            #     self._add_windows_config()
            #
            # self._replace_epics_base()
            # self._set_extra_options()
            #
            # autotools = AutoToolsBuildEnvironment(self)
            # env_build = RunEnvironment(self)
            #
            # # propagate changes through modules
            # with tools.chdir('synApps/support'):
            #     autotools.make(target='release', vars=env_build.vars)
            #
            # self._comment_unwanted_modules()
            # self.modules = self._list_wanted_modules()
            #
            # with tools.chdir('synApps/support'):
            #     autotools.make(vars=env_build.vars)

            #    def package(self):
            #
            #        if tools.os_info.is_linux:
            #            arch = "linux-x86_64"
            #        elif tools.os_info.is_macos:
            #            arch = "darwin-x86"
            #
            #        for module in self._list_wanted_modules():
            #            path = os.path.join('synApps/support', module, 'lib', arch)
            #            if os.path.isdir(path):
            #                self.copy("*.a", dst="lib", src=path, keep_path=False)
            #                self.copy("*.so", dst="lib", src=path, keep_path=False)
            #                self.copy("*.dylib", dst="lib", src=path, keep_path=False)
            #            path = os.path.join('synApps/support', module, 'include')
            #            if os.path.isdir(path):
            #                self.copy("*.h", dst="include", src=path, keep_path=False)
            #
            #    def package_info(self):
            #        self.cpp_info.libs = self.collect_libs()
            #

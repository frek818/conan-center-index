import os
from conans import ConanFile, CMake, tools
import re
import shutil


class TermcapConan(ConanFile):
    name = "termcap"
    homepage = "https://www.gnu.org/software/termcap"
    url = "https://github.com/conan-io/conan-center-index"
    description = "Enables programs to use display terminals in a terminal-independent manner"
    license = "GPL-2.0"
    topics = ("conan", "termcap", "terminal", "display")
    exports_sources = ["CMakeLists.txt", "patches/*"]
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False], }
    default_options = {"shared": False, "fPIC": True, }

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def source(self):
        archive_name = self.name + "-" + self.version
        tools.get(**self.conan_data["sources"][self.version])
        os.rename(archive_name, self._source_subfolder)

    def _extract_sources(self):
        makefile_text = open(os.path.join(self._source_subfolder, "Makefile.in")).read()
        sources = list("{}/{}".format(self._source_subfolder, src) for src in re.search("\nSRCS = (.*)\n", makefile_text).group(1).strip().split(" "))
        headers = list("{}/{}".format(self._source_subfolder, src) for src in re.search("\nHDRS = (.*)\n", makefile_text).group(1).strip().split(" "))
        autoconf_text = open(os.path.join(self._source_subfolder, "configure.in")).read()
        optional_headers = re.search(r"AC_HAVE_HEADERS\((.*)\)", autoconf_text).group(1).strip().split(" ")
        return sources, headers, optional_headers

    def _configure_cmake(self):
        cmake = CMake(self)
        sources, headers, optional_headers = self._extract_sources()
        cmake.definitions["TERMCAP_SOURCES"] = ";".join(sources)
        cmake.definitions["TERMCAP_HEADERS"] = ";".join(headers)
        cmake.definitions["TERMCAP_INC_OPTS"] = ";".join(optional_headers)
        cmake.verbose=True
        cmake.parallel = False
        cmake.configure()
        return cmake

    def _patch_sources(self):
        for patch in self.conan_data["patches"][self.version]:
            tools.patch(**patch)
        for src in self._extract_sources()[0]:
            txt = open(src).read()
            with open(src, "w") as f:
                f.write("#include \"termcap_intern.h\"\n\n")
                f.write(txt)

    def build(self):
        self._patch_sources()
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="COPYING", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "Termcap"
        self.cpp_info.names["cmake_find_package_multi"] = "Termcap"
        self.cpp_info.libs = tools.collect_libs(self)
        if self.options.shared:
            self.cpp_info.definitions = ["TERMCAP_SHARED"]

%define _requires_exceptions	libR\\|libf77blas\\|devel(

# svn trunk
%define svnsnapshot	4579

%define name		elmer
%define version		5.4.1.%{svnsnapshot}

%define eio_incs	-I%{_builddir}/%{name}-%{version}/eio/include
%define eioc_libs	-L%{_builddir}/%{name}-%{version}/eio/src -leioc
%define eiof_libs	-L%{_builddir}/%{name}-%{version}/eio/src -leiof

%define huti_incs	-I%{_builddir}/%{name}-%{version}/hutiter/src
%define huti_libs	-L%{_builddir}/%{name}-%{version}/hutiter/src -lhuti

%define matc_incs	-I%{_builddir}/%{name}-%{version}/matc/src
%define matc_libs	-L%{_builddir}/%{name}-%{version}/matc/src -lmatc -lm

%define arpack_libs	-L%{_builddir}/%{name}-%{version}/mathlibs/src/arpack -larpack
%define parpack_libs	-L%{_builddir}/%{name}-%{version}/mathlibs/src/parpack -lparpack -lmpi_f77 -lmpi_f90
%define elmerparam_incs	-I%{_builddir}/%{name}-%{version}/elmerparam/src
%define elmerparam_libs	-L%{_builddir}/%{name}-%{version}/elmerparam/src -lelmerparam

%define modules		matc mathlibs elmergrid meshgen2d eio hutiter fem post elmerparam front

%define		ELMER_HOME		%{_datadir}/%{name}
%define		ELMERGUI_HOME		%{ELMER_HOME}
%define		ELMER_POST_HOME		%{ELMER_HOME}

Name:		%{name}
Group:		Sciences/Physics
License:	GPL
Summary:	Open Source Finite Element Software for Multiphysical Problems
Version:	%{version}
Release:	%mkrel 2
URL:		http://www.csc.fi/english/pages/elmer
Source0:	elmer-%{version}.tar.bz2
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

#-----------------------------------------------------------------------
BuildRequires:	R-base
BuildRequires:	amd-devel
BuildRequires:	ftgl-devel
BuildRequires:	gcc-gfortran
BuildRequires:	libatlas-devel
BuildRequires:	libqwt-devel
BuildRequires:	libopencascade-devel
BuildRequires:	openmpi-devel
BuildRequires:	python-qt
BuildRequires:	qt4-devel
BuildRequires:	readline-devel
BuildRequires:	tcl-devel
BuildRequires:	tk-devel
BuildRequires:	umfpack-devel
BuildRequires:	vtk-devel
%py_requires -d
Requires:	libatlas
Requires:	R-base

#-----------------------------------------------------------------------
Patch0:		elmer-5.4.x-tcl8.6.patch
Patch1:		elmer-5.4.x-install.patch
Patch2:		elmer-5.4.x-check-argv.patch
Patch3:		elmer-5.4.x-qt4.patch
Patch4:		elmer-5.4.x-format.patch
Patch5:		elmer-5.4.x-env.patch
Patch6:		elmer-5.4.x-tester.patch
Patch7:		elmer-5.4.x-keywords.patch

#-----------------------------------------------------------------------
%description
Elmer is an open source multiphysical simulation software developed by CSC.
Elmer development was started 1995 in collaboration with Finnish Universities,
research institutes and industry.

Elmer includes physical models of fluid dynamics, structural mechanics,
electromagnetics, heat transfer and acoustics, for example. These are
described by partial differential equations which Elmer solves by the
Finite Element Method (FEM).

#------------------------------------------------------------------------
%prep
%setup -q

%patch0 -p1
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1
%patch6 -p1
%patch7 -p1

#------------------------------------------------------------------------
%build
export ELMER_HOME=%{ELMER_HOME}
export ELMERGUI_HOME=%{ELMERGUI_HOME}
export ELMER_POST_HOME=%{ELMER_POST_HOME}
export CC=gcc; export CXX=g++; export FC=gfortran; export F77=gfortran

# elmerparam doesn't use --with-matc
perl -pi						\
	-e 's|-L\@prefix\@/lib -lmatc|%{matc_libs}|;'	\
	elmerparam/src/Makefile.in

for m in %{modules}; do
    pushd $m
    %configure						\
	--prefix=%{ELMER_HOME}				\
	--with-mpi					\
	--with-mpidir=%{_prefix}			\
	--with-mpi-lib-dir=%{_libdir}			\
	--with-blas='-L%{_libdir}/atlas -lf77blas'	\
	--with-lapack='-L%{_libdir}/atlas -llapack'	\
	--with-tcltk='-L%{_libdir} -ltcl -ltk'		\
	--with-huti='%{huti_libs}'			\
	--with-eioc='%{eioc_libs}'			\
	--with-eiof='%{eiof_libs}'			\
	--with-arpack='%{arpack_libs}'			\
	--with-parpack='%{parpack_libs}'		\
	--with-matc='%{matc_libs}'
    make						\
	CXXFLAGS='%{eio_incs} %{huti_incs} %{matc_incs} -fPIC'	\
	CFLAGS='%{eio_incs} %{huti_incs} %{matc_incs} -fPIC'	\
	FFLAGS="-fopenmp -fPIC"				\
	FCPPFLAGS='-P -traditional-cpp -I. %{huti_incs} -DFULL_INDUCTION -DUSE_ARPACK'
    popd
done

pushd ElmerGUI
    %ifarch x86_64 ppc64
    perl -pi						\
	-e 's|/usr/lib\b|%{_libdir}|;'			\
	-e 's|(BITS =) 32|$1 64|;'			\
	ElmerGUI.pri
    %endif
    CXXFLAGS=-fPIC qmake

    # Even adding libraries multiple times in command line doesn't
    # correct linking; should correct the libraries themselves?!
    make Application/Makefile
    perl -pi						\
	-e 's|-Wl,--as-needed||;'			\
	Application/Makefile

    make
popd

pushd ElmerGUIlogger
    qmake -project
    qmake
    make
popd

pushd ElmerGUItester
    qmake
    make
popd

pushd misc/tetgen_plugin
    qmake
    make
popd

#------------------------------------------------------------------------
%install
export ELMER_HOME=%{ELMER_HOME}
export ELMERGUI_HOME=%{ELMERGUI_HOME}
export ELMER_POST_HOME=%{ELMER_POST_HOME}

mkdir -p %{buildroot}%{ELMER_HOME}/{bin,lib,include} %{buildroot}%{_libdir}/R

perl -pi								\
	-e 's|%{ELMER_HOME}/lib/R|\$(DESTDIR)%{_libdir}/R|;'		\
	elmerparam/src/R/Makefile
perl -pi								\
	-e 's|(PKG_CPPFLAGS = ).*|$1%{elmerparam_incs}|;'		\
	-e 's|(PKG_LIBS = ).*|$1%{elmerparam_libs} %{matc_libs}|;'	\
	elmerparam/src/R/elmerparam/src/Makevars

perl -pi								\
	-e 's|/usr/local/|%{_prefix}/|g;'				\
	ElmerGUI/Application/Makefile

export CC=gcc; export CXX=g++; export FC=gfortran; export F77=gfortran
for m in %{modules} ElmerGUI ElmerGUIlogger ElmerGUItester misc/tetgen_plugin; do
    pushd $m
%makeinstall_std INSTALL_ROOT=%{buildroot}
    popd
done

# cannot disable build of these
rm -f %{buildroot}%{_libdir}/lib{blas,lapack}.a

mv -f %{buildroot}%{ELMERGUI_HOME}/ElmerGUI %{buildroot}%{ELMERGUI_HOME}/bin
mv -f %{buildroot}%{_bindir}/* %{buildroot}%{ELMERGUI_HOME}/bin

cp -far ElmerGUI/Application/ElmerGUI ElmerGUIlogger/ElmerGUIlogger ElmerGUItester/ElmerGUItester %{buildroot}%{ELMERGUI_HOME}/bin
cp -far ElmerGUI/Application/edf-extra %{buildroot}%{ELMERGUI_HOME}

for script in ElmerGUI ElmerGUIlogger ElmerGUItester; do
cat > %{buildroot}%{_bindir}/$script << EOF
#!/bin/sh

export ELMER_HOME=%{ELMER_HOME}
export ELMERGUI_HOME=%{ELMERGUI_HOME}
export ELMER_POST_HOME=%{ELMER_POST_HOME}
export PATH=%{ELMER_HOME}/bin:\$PATH
export LD_LIBRARY_PATH=%{ELMER_HOME}/lib:\$LD_LIBRARY_PATH
%{ELMER_HOME}/bin/$script "\$@"
EOF
chmod +x %{buildroot}%{_bindir}/$script
done
ln -sf %{_bindir}/ElmerGUI %{buildroot}%{_bindir}/%{name}

cp -far ElmerGUI/{samples,scripts} %{buildroot}%{ELMERGUI_HOME}

#------------------------------------------------------------------------
%clean
rm -rf %{buildroot}

#------------------------------------------------------------------------
%files
%defattr(-,root,root)
%{_bindir}/*
%{_includedir}/*.h
%{_includedir}/*.mod
%dir %{_includedir}/elmer
%{_includedir}/elmer/*.h
%{_libdir}/*.a
%{_libdir}/R/R.css
%dir %{_libdir}/R/elmerparam
%{_libdir}/R/elmerparam/*
%dir %{ELMER_HOME}
%{ELMER_HOME}/*

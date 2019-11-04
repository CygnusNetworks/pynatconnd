%if 0%{?rhel} && 0%{?rhel} <= 7
%{!?py2_build: %global py2_build %{__python2} setup.py build}
%{!?py2_install: %global py2_install %{__python2} setup.py install --skip-build --root %{buildroot}}
%endif

%if (0%{?fedora} >= 21 || 0%{?rhel} >= 8)
%global with_python3 1
%endif

%define srcname natconnd
%define pkgname py%{srcname}
%define version 0.15
%define release 1
%define sum Cygnus Networks GmbH %{pkgname} package

Name:           python-%{srcname}
Version:        %{version}
Release:        %{release}%{?dist}
Summary:        %{sum}
License:        proprietary
Source0:        python-%{srcname}-%{version}.tar.gz

BuildArch:      x86_64
BuildRequires:  python2-devel, python-setuptools, python-cffi, libnfnetlink-devel, libnetfilter_conntrack-devel
%{?systemd_requires}
BuildRequires: systemd
%if 0%{?with_check}
BuildRequires:  pytest
%endif # with_check
Requires:       python-setuptools, python-configobj, python-ipaddress, python-cffi, python2-falcon, python2-future

%{?python_provide:%python_provide python-%{project}}

%if 0%{?with_python3}
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
%if 0%{?with_check}
BuildRequires:  python3-pytest
%endif # with_check
%endif # with_python3

%description
%{sum}

%if 0%{?with_python3}
%package -n python3-%{project}
Summary:        %{sum}
%{?python_provide:%python_provide python3-%{project}}
Requires:       python3-setuptools

%description -n python3-%{project}
%{sum}
%endif # with_python3

%prep
%setup -q -n python-%{srcname}-%{version}

%build
%py2_build

%if 0%{?with_python3}
%py3_build
%endif # with_python3


%install
%py2_install
mkdir -p $RPM_BUILD_ROOT%{_unitdir}
install -p -m 644 ./debian/service $RPM_BUILD_ROOT%{_unitdir}/pynatconnd.service
%if 0%{?with_python3}
%py3_install
mkdir -p $RPM_BUILD_ROOT%{_unitdir}
install -p -m 644 ./debian/service $RPM_BUILD_ROOT%{_unitdir}/pynatconnd.service
%endif # with_python3

%if 0%{?with_check}
%check
LANG=en_US.utf8 py.test-%{python2_version} -vv tests

%if 0%{?with_python3}
LANG=en_US.utf8 py.test-%{python3_version} -vv tests
%endif # with_python3
%endif # with_check

%post
%systemd_post pynatconnd.service

%preun
%systemd_preun pynatconnd.service

%postun
%systemd_postun_with_restart pynatconnd.service

%files
%dir %{python2_sitearch}/%{srcname}
%{python2_sitearch}/_cffi_*.so
%{python2_sitearch}/%{srcname}/*.*
%{python2_sitearch}/%{pkgname}-%{version}-py2.*.egg-info
%{_unitdir}/pynatconnd.service
%{_bindir}/pynatconnd

%if 0%{?with_python3}
%files -n python3-%{project}
%dir %{python3_sitearch}/%{srcname}
%dir %{python3_sitearch}/%{srcname}/__pycache__
%{python3_sitearch}/_cffi_*.so
%{python3_sitearch}/%{srcname}/*.*
%{python3_sitearch}/%{srcname}/__pycache__/*.py*
%{python3_sitearch}/%{pkgname}-%{version}-py3.*.egg-info
%{_unitdir}/pynatconnd.service
%{_bindir}/pynatconnd
%endif # with_python3

%changelog

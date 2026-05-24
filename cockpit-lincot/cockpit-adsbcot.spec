Name: cockpit-adsbcot
Version: 1.0.8
Release: 1%{?dist}
Summary: Cockpit ADSBCOT Module
License: Apache-2.0

Source0: https://github.com/snstac/cockpit-adsbcot/releases/download/%{version}/%{name}-%{version}.tar.xz
Source1: https://github.com/snstac/cockpit-adsbcot/releases/download/%{version}/%{name}-node-%{version}.tar.xz
BuildArch: noarch
%if ! 0%{?suse_version}
ExclusiveArch: %{nodejs_arches} noarch
%endif
%if ! 0%{?rhel} || 0%{?rhel} >= 10
BuildRequires: nodejs >= 18
%endif
BuildRequires: make
%if 0%{?suse_version}
# Suse's package has a different name
BuildRequires: appstream-glib
%else
BuildRequires: libappstream-glib
%endif
BuildRequires: gettext
%if 0%{?rhel} && 0%{?rhel} <= 8
BuildRequires: libappstream-glib-devel
%endif

Requires: cockpit-bridge

Provides: bundled(npm(attr-accept)) = 2.2.5
Provides: bundled(npm(file-selector)) = 2.1.2
Provides: bundled(npm(focus-trap)) = 7.6.2
Provides: bundled(npm(js-tokens)) = 4.0.0
Provides: bundled(npm(loose-envify)) = 1.4.0
Provides: bundled(npm(object-assign)) = 4.1.1
Provides: bundled(npm(@patternfly/patternfly)) = 6.1.0
Provides: bundled(npm(@patternfly/react-core)) = 6.1.0
Provides: bundled(npm(@patternfly/react-icons)) = 6.1.0
Provides: bundled(npm(@patternfly/react-styles)) = 6.3.1
Provides: bundled(npm(@patternfly/react-tokens)) = 6.4.0
Provides: bundled(npm(prop-types)) = 15.8.1
Provides: bundled(npm(react)) = 18.3.1
Provides: bundled(npm(react-dom)) = 18.3.1
Provides: bundled(npm(react-dropzone)) = 14.4.1
Provides: bundled(npm(react-is)) = 16.13.1
Provides: bundled(npm(scheduler)) = 0.23.2
Provides: bundled(npm(tabbable)) = 6.4.0
Provides: bundled(npm(tslib)) = 2.8.1

%description
Cockpit ADSBCOT Module

%prep
%autosetup -n %{name} -a 1
# ignore pre-built bundle in release tarball and rebuild it
# but keep it in RHEL/CentOS-8/9, as that has a too old nodejs
%if ! 0%{?rhel} || 0%{?rhel} >= 10
rm -rf dist
%endif

%build
NODE_ENV=production make

%install
%make_install PREFIX=/usr

# drop source maps, they are large and just for debugging
find %{buildroot}%{_datadir}/cockpit/ -name '*.map' | xargs --no-run-if-empty rm --verbose

%check
appstream-util validate-relax --nonet %{buildroot}/%{_datadir}/metainfo/*

# this can't be meaningfully tested during package build; tests happen through
# FMF (see plans/all.fmf) during package gating

%files
%doc README.md
%license LICENSE dist/index.js.LEGAL.txt
%{_datadir}/cockpit/*
%{_datadir}/metainfo/*
%{_datadir}/polkit-1/rules.d/49-cockpit-adsbcot.rules

%changelog

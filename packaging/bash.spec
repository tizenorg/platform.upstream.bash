Name:           bash
Version:        4.2
Release:        1
License:        GPL-3.0+
Summary:        The GNU Bourne Again shell
Url:            http://www.gnu.org/software/bash
Group:          Base/Tools
Source0:        ftp://ftp.gnu.org/gnu/bash/%{name}-%{version}.tar.gz
Source1:        dot.bashrc
Source2:        dot.profile
BuildRequires:  autoconf
BuildRequires:  bison
Provides:	/bin/bash
Provides:	/bin/sh

%description
The GNU Bourne Again shell (Bash) is a shell or command language
interpreter that is compatible with the Bourne shell (sh). Bash
incorporates useful features from the Korn shell (ksh) and the C shell
(csh). Most sh scripts can be run by bash without modification.


%prep
%setup -q

%build
%configure --enable-largefile \
            --without-bash-malloc \
            --disable-nls \
            --enable-alias \
            --enable-readline  \
            --enable-history

# Recycles pids is neccessary. When bash's last fork's pid was X
# and new fork's pid is also X, bash has to wait for this same pid.
# Without Recycles pids bash will not wait.
make "CPPFLAGS=-D_GNU_SOURCE -DDEFAULT_PATH_VALUE='\"/usr/local/bin:/usr/bin\"' -DRECYCLES_PIDS `getconf LFS_CFLAGS`"
%check
make check

%install
%make_install

mkdir -p %{buildroot}/etc

#mkdir -p %{buildroot}/%{_bindir}
#mv %{buildroot}/bin/* %{buildroot}/%{_bindir}/

# make manpages for bash builtins as per suggestion in DOC/README
pushd doc
sed -e '
/^\.SH NAME/, /\\- bash built-in commands, see \\fBbash\\fR(1)$/{
/^\.SH NAME/d
s/^bash, //
s/\\- bash built-in commands, see \\fBbash\\fR(1)$//
s/,//g
b
}
d
' builtins.1 > man.pages
for i in echo pwd test kill; do
  perl -pi -e "s,$i,,g" man.pages
  perl -pi -e "s,  , ,g" man.pages
done

install -c -m 644 builtins.1 %{buildroot}%{_mandir}/man1/builtins.1

for i in `cat man.pages` ; do
  echo .so man1/builtins.1 > %{buildroot}%{_mandir}/man1/$i.1
  chmod 0644 %{buildroot}%{_mandir}/man1/$i.1
done
popd

# Link bash man page to sh so that man sh works.
ln -s bash.1 %{buildroot}%{_mandir}/man1/sh.1

# Not for printf, true and false (conflict with coreutils)
rm -f %{buildroot}/%{_mandir}/man1/printf.1
rm -f %{buildroot}/%{_mandir}/man1/true.1
rm -f %{buildroot}/%{_mandir}/man1/false.1

pushd %{buildroot}
ln -sf bash ./usr/bin/sh
rm -f .%{_infodir}/dir
popd
mkdir -p %{buildroot}%{_sysconfdir}/skel
install -c -m644 %{SOURCE1} %{buildroot}%{_sysconfdir}/skel/.bashrc
install -c -m644 %{SOURCE2} %{buildroot}%{_sysconfdir}/skel/.bash_profile
LONG_BIT=$(getconf LONG_BIT)
mv %{buildroot}%{_bindir}/bashbug \
   %{buildroot}%{_bindir}/bashbug-"${LONG_BIT}"

# Fix missing sh-bangs in example scripts (bug #225609).
for script in \
  examples/scripts/krand.bash \
  examples/scripts/bcsh.sh \
  examples/scripts/precedence \
  examples/scripts/shprompt
do
  cp "$script" "$script"-orig
  echo '#!/bin/bash' > "$script"
  cat "$script"-orig >> "$script"
  rm -f "$script"-orig
done

rm -rf %{buildroot}%{_bindir}/bashbug-*
chmod a-x doc/*.sh

%docs_package

%post -p <lua>
bashfound = false;
shfound = false;

f = io.open("/etc/shells", "r");
if f == nil
then
  f = io.open("/etc/shells", "w");
else
  repeat
    t = f:read();
    if t == "/bin/bash"
    then
      bashfound = true;
    end
    if t == "/bin/sh"
    then
      shfound = true;
    end
  until t == nil;
end
f:close()

f = io.open("/etc/shells", "a");
if not bashfound
then
  f:write("/bin/bash\n")
end
if not shfound
then
  f:write("/bin/sh\n")
end
f:close()

%postun
if [ "$1" = 0 ]; then
    /bin/grep -v '^/bin/bash$' < /etc/shells | \
      /bin/grep -v '^/bin/sh$' > /etc/shells.new
    /bin/mv /etc/shells.new /etc/shells
fi



%files
%license COPYING
%{_bindir}/sh
%{_bindir}/bash
%{_sysconfdir}/skel

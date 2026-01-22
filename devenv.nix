{ ... }:
let
  shell = { pkgs, ... }: {
    languages.python.enable = true;
    languages.python.uv.enable = true;
  };
  devcontainer = { ... }: {
    devcontainer.enable = true;
  };
in
{
  profiles.shell.module = {
    imports = [ shell ];
  };
  profiles.devcontainer.module = {
    imports = [ devcontainer ];
  };
}

{ pkgs, ... }:

{
  # Tools used by the PetClinic, I Hate Money, and OpenSpec workshop branches.
  packages = with pkgs; [
    jdk17
    uv
    nodejs_24
  ];
}

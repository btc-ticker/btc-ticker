variable "pack" { default = "lean" }
variable "github_user" { default = "btc-ticker" }
variable "branch" { default = "main" }
variable "image_link" { default = "https://downloads.raspberrypi.org/raspios_oldstable_armhf/images/raspios_oldstable_armhf-2025-05-07/2025-05-06-raspios-bullseye-armhf.img.xz" }
variable "image_checksum" { default = "1e9e1e3beaae46bd9ae999b63ad221b43163f37e31189bf9a36d258dcb96f85c" }
variable "image_size" { default = "24G" }

source "arm" "btcticker-armhf-rpi" {
  file_checksum_type    = "sha256"
  file_checksum         = var.image_checksum
  file_target_extension = "xz"
  file_unarchive_cmd    = ["xz", "--decompress", "$ARCHIVE_PATH"]
  file_urls             = [var.image_link]
  image_build_method    = "resize"
  image_chroot_env      = ["PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"]
  image_partitions {
    filesystem   = "vfat"
    mountpoint   = "/boot"
    name         = "boot"
    size         = "256M"
    start_sector = "8192"
    type         = "c"
  }
  image_partitions {
    filesystem   = "ext4"
    mountpoint   = "/"
    name         = "root"
    size         = "0"
    start_sector = "532480"
    type         = "83"
  }
  image_path                   = "btcticker-armhf-rpi-${var.pack}.img"
  image_size                   = var.image_size
  image_type                   = "dos"
  qemu_binary_destination_path = "/usr/bin/qemu-arm-static"
  qemu_binary_source_path      = "/usr/bin/qemu-arm-static"
}

build {
  sources = ["source.arm.btcticker-armhf-rpi"]

  provisioner "shell" {
    inline = [
      "echo 'nameserver 1.1.1.1' > /etc/resolv.conf",
      "echo 'nameserver 8.8.8.8' >> /etc/resolv.conf",
      "echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections",
      "apt-get update",
      "apt-get install -y sudo wget",
      "apt-get -y autoremove",
      "apt-get -y clean",
      "touch /boot/ssh",
    ]
  }

  provisioner "shell" {
    environment_vars = [
      "github_user=${var.github_user}",
      "branch=${var.branch}",
      "pack=${var.pack}"
    ]
    script = "./build.btcticker.sh"
  }

  provisioner "shell" {
    inline = [
      "echo '# delete the SSH keys (will be recreated on the first boot)'",
      "rm -f /etc/ssh/ssh_host_*",
      "echo 'OK'",
    ]
  }

  provisioner "shell" {
    inline = [
      "if [ \"${var.pack}\" = \"base\" ]; then echo 'Adding stop file to /boot/'; touch /boot/stop; fi"
    ]
  }
}

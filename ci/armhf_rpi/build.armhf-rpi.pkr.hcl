variable "pack" { default = "lean" }
variable "github_user" { default = "btc-ticker" }
variable "branch" { default = "main" }
variable "image_link" { default = "https://downloads.raspberrypi.org/raspios_oldstable_armhf/images/raspios_oldstable_armhf-2023-12-06/2023-12-05-raspios-bullseye-armhf.img.xz" }
variable "image_checksum" { default = "f5ee1b7b46f206612c985656d0c78c07b108b5953e4f155d5fe0e78468b97d9a" }

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
  image_size                   = "12G"
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
}

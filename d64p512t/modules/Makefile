FPGA_MODULE_NAME = d64p512t_fpga
$(FPGA_MODULE_NAME)-y := fpga.o fpga_attr.o fpga_gpio.o fpga_i2c.o fpga_reg.o

obj-m := $(FPGA_MODULE_NAME).o pddf_custom_sysstatus_module.o

CFLAGS_pddf_custom_sysstatus_module.o := -I$(M)/../../../../pddf/i2c/modules/include

VERSION_GE_6_12 := $(shell echo $(KERNELRELEASE) | awk -F. '{ printf("%d", ($$1 > 6 || ($$1 == 6 && $$2 >= 12))) }')

ifeq ($(VERSION_GE_6_12),1)
KBUILD_EXTRA_SYMBOLS := $(KERNEL_SRC)/Module.symvers.PDDF
else
KBUILD_EXTRA_SYMBOLS := $(M)/../../../../pddf/i2c/Module.symvers.PDDF
endif

FPGA_MODULE_NAME = d64p512t_fpga
$(FPGA_MODULE_NAME)-y := fpga.o fpga_attr.o fpga_gpio.o fpga_i2c.o fpga_reg.o

obj-m := $(FPGA_MODULE_NAME).o d64p512t_i2c-i801.o \
         pddf_custom_sysstatus_module.o

CFLAGS_pddf_custom_sysstatus_module.o := -I$(M)/../../../../pddf/i2c/modules/include
KBUILD_EXTRA_SYMBOLS := $(M)/../../../../pddf/i2c/Module.symvers.PDDF

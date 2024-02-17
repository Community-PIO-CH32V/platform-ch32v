
#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>

/* 1000 msec = 1 sec */
#define SLEEP_TIME_MS 1000

/* The devicetree node identifier for the "led_custom" alias.
   This pin is being defined in zephyr/boards/usb_pdmon.overlay as PB1.
   Can also use the following aliases
   led0 = ledr = PA7 
   led1 = ledb = PB3 
   led2 = ledg = PB0 
 */
#define LED_NODE DT_ALIAS(ledcustom)

/*
 * A build error on this line means your board is unsupported.
 * See the sample documentation for information on how to fix this.
 */
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(LED_NODE, gpios);

static unsigned cnt = 0;

void main(void)
{
	int ret;

	if (!gpio_is_ready_dt(&led))
	{
		return;
	}

	ret = gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
	if (ret < 0)
	{
		return;
	}
	while (1)
	{
		ret = gpio_pin_toggle_dt(&led);
		if (ret < 0)
		{
			return;
		}
		/* UART output on PA2 at 115200 baud */
		/* per overlay file */
		printk("Toggled LED! %u\n", cnt++);
 		k_msleep(SLEEP_TIME_MS);
	}
}
#import "PQGiftsStore.h"

static NSString *const kKey = @"puzzlequest.gifts";

@implementation PQGiftsStore

+ (instancetype)sharedStore
{
    static PQGiftsStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQGiftsStore alloc] init];
    });
    return shared;
}

- (NSInteger)pending
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setPending:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end

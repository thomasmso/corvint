#import "PQChestsStore.h"

static NSString *const kKey = @"puzzlequest.chests";

@implementation PQChestsStore

+ (instancetype)sharedStore
{
    static PQChestsStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQChestsStore alloc] init];
    });
    return shared;
}

- (NSInteger)unopened
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setUnopened:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
